#!/usr/bin/env bun
import { Command } from "commander";
import { getAuthClient, getAuthStatus, login, logout } from "./auth";
import { error, exitCode, output, success } from "./output";
import {
  batchUpdate,
  clearAndSetText,
  copyPresentation,
  deleteElement,
  deleteSlide,
  deleteSlides,
  duplicateSlide,
  extractAllText,
  findPresentations,
  getAllSlides,
  getDriveClient,
  getPresentation,
  getSlide,
  getSlidesClient,
  getSlidesThumbnails,
  insertImage,
  listLayouts,
  moveToFolder,
  reorderSlides,
  replaceAllText,
  setSpeakerNotes,
  sharePresentation,
  sharePresentationWithDomain,
  updateElementTransform,
  updateTextStyle,
} from "./slides";
import type { Result, SlideReplacement } from "./types";
import { parsePresentationId } from "./types";

const CLI_VERSION = "1.0.0";
const program = new Command();

/**
 * Unescape common escape sequences in CLI string arguments.
 * When the shell passes --text "line1\nline2", the CLI receives the literal
 * characters backslash+n. This function converts them to actual newlines/tabs.
 */
function unescapeText(text: string): string {
  return text.replace(/\\n/g, "\n").replace(/\\t/g, "\t");
}

function resolvePresentation(
  cmd: string,
  input: string | undefined
): string | null {
  if (!input) {
    output(
      error(
        cmd,
        "VALIDATION_ERROR",
        "Presentation ID required. Use --presentation <id-or-url>."
      )
    );
    return null;
  }
  return parsePresentationId(input);
}

function handleApiError(
  cmd: string,
  err: unknown,
  presentationId?: string
): Result {
  const message = err instanceof Error ? err.message : String(err);
  const maybe = err as {
    code?: string;
    response?: { status?: number; data?: unknown };
  };
  const status = maybe.response?.status;

  if (
    message.includes("invalid_grant") ||
    message.includes("Token has been expired") ||
    status === 401
  ) {
    return error(
      cmd,
      "AUTH_ERROR",
      "Auth expired. Run 'slides-cli auth login'.",
      { presentationId, status }
    );
  }
  if (status === 403 || message.toLowerCase().includes("permission")) {
    return error(cmd, "PERMISSION_ERROR", message, {
      presentationId,
      status,
    });
  }
  return error(cmd, "API_ERROR", message, { presentationId, status });
}

async function getSlides(cmd: string) {
  const client = await getAuthClient();
  if (!client) {
    output(
      error(
        cmd,
        "AUTH_ERROR",
        "Not authenticated. Run 'slides-cli auth login' first."
      )
    );
    return null;
  }
  return { slides: getSlidesClient(client), drive: getDriveClient(client), auth: client };
}

program
  .name("slides-cli")
  .description(
    `CLI for Google Slides primitives

Presentation ID:
  Most commands accept --presentation <id> to specify the target.
  Get the ID from your presentation URL: docs.google.com/presentation/d/<ID>/edit
  You can also pass the full URL directly.`
  )
  .version(CLI_VERSION);

// ── Auth commands ──

const auth = program.command("auth").description("Authentication commands");

auth
  .command("login")
  .description("Authenticate with Google")
  .requiredOption("--credentials <path>", "Path to OAuth client JSON file")
  .option("--token-store <path>", "Path to store token")
  .action(async (opts) => {
    const result = await login(opts.credentials, opts.tokenStore);
    if (result.success) {
      output(success("auth login", { message: result.message }));
      process.exit(0);
    } else {
      output(error("auth login", "AUTH_ERROR", result.message));
      process.exit(20);
    }
  });

auth
  .command("status")
  .description("Check authentication status")
  .action(async () => {
    const status = await getAuthStatus();
    output(success("auth status", status));
    process.exit(0);
  });

auth
  .command("logout")
  .description("Clear stored credentials")
  .option("--token-store <path>", "Token storage path")
  .action(async (opts: { tokenStore?: string }) => {
    const result = await logout(opts.tokenStore);
    if (result.success) {
      output(success("auth logout", { message: result.message }));
      process.exit(0);
    } else {
      output(error("auth logout", "AUTH_ERROR", result.message));
      process.exit(20);
    }
  });

// ── Presentation info commands ──

const pres = program.command("presentation").description("Presentation metadata");

pres
  .command("info")
  .description("Get presentation metadata and slide overview")
  .requiredOption("--presentation <id>", "Presentation ID or URL")
  .action(async (opts) => {
    const cmd = "presentation info";
    const presId = resolvePresentation(cmd, opts.presentation);
    if (!presId) return process.exit(10);
    const clients = await getSlides(cmd);
    if (!clients) return process.exit(20);

    try {
      const info = await getPresentation(clients.slides, presId);
      output(success(cmd, info, { presentationId: presId }));
      process.exit(0);
    } catch (err) {
      const result = handleApiError(cmd, err, presId);
      output(result);
      process.exit(exitCode(result));
    }
  });

pres
  .command("find")
  .description("Search for presentations by name (uses Drive API)")
  .requiredOption("--name <query>", "Name to search for")
  .option("--limit <n>", "Max results", "10")
  .action(async (opts) => {
    const cmd = "presentation find";
    const clients = await getSlides(cmd);
    if (!clients) return process.exit(20);

    try {
      const limit = Number.parseInt(opts.limit, 10);
      const presentations = await findPresentations(clients.drive, opts.name, limit);
      output(
        success(cmd, {
          query: opts.name,
          count: presentations.length,
          presentations,
        })
      );
      process.exit(0);
    } catch (err) {
      const result = handleApiError(cmd, err);
      output(result);
      process.exit(exitCode(result));
    }
  });

// ── Layout commands ──

program
  .command("layouts")
  .description("List available slide layouts and their placeholders")
  .requiredOption("--presentation <id>", "Presentation ID or URL")
  .action(async (opts) => {
    const cmd = "layouts";
    const presId = resolvePresentation(cmd, opts.presentation);
    if (!presId) return process.exit(10);
    const clients = await getSlides(cmd);
    if (!clients) return process.exit(20);

    try {
      const layouts = await listLayouts(clients.slides, presId);
      output(success(cmd, { layouts }, { presentationId: presId }));
      process.exit(0);
    } catch (err) {
      const result = handleApiError(cmd, err, presId);
      output(result);
      process.exit(exitCode(result));
    }
  });

// ── Read commands ──

const read = program.command("read").description("Read data from presentations");

read
  .command("slide")
  .description("Read a specific slide's elements and text (use --all for all slides)")
  .requiredOption("--presentation <id>", "Presentation ID or URL")
  .option("--index <n>", "Slide index (0-based)")
  .option("--all", "Read all slides at once")
  .action(async (opts) => {
    const cmd = "read slide";
    const presId = resolvePresentation(cmd, opts.presentation);
    if (!presId) return process.exit(10);
    const clients = await getSlides(cmd);
    if (!clients) return process.exit(20);

    if (opts.all) {
      try {
        const allSlides = await getAllSlides(clients.slides, presId);
        output(success(cmd, { slideCount: allSlides.length, slides: allSlides }, { presentationId: presId }));
        process.exit(0);
      } catch (err) {
        const result = handleApiError(cmd, err, presId);
        output(result);
        process.exit(exitCode(result));
      }
      return;
    }

    if (opts.index === undefined) {
      output(error(cmd, "VALIDATION_ERROR", "Provide --index <n> or --all"));
      return process.exit(10);
    }

    const index = Number.parseInt(opts.index, 10);
    if (!Number.isFinite(index) || index < 0) {
      output(error(cmd, "VALIDATION_ERROR", "Invalid slide index"));
      return process.exit(10);
    }

    try {
      const slide = await getSlide(clients.slides, presId, index);
      output(success(cmd, slide, { presentationId: presId }));
      process.exit(0);
    } catch (err) {
      const result = handleApiError(cmd, err, presId);
      output(result);
      process.exit(exitCode(result));
    }
  });

read
  .command("text")
  .description("Extract all text content from all slides")
  .requiredOption("--presentation <id>", "Presentation ID or URL")
  .action(async (opts) => {
    const cmd = "read text";
    const presId = resolvePresentation(cmd, opts.presentation);
    if (!presId) return process.exit(10);
    const clients = await getSlides(cmd);
    if (!clients) return process.exit(20);

    try {
      const textData = await extractAllText(clients.slides, presId);
      output(success(cmd, { slides: textData }, { presentationId: presId }));
      process.exit(0);
    } catch (err) {
      const result = handleApiError(cmd, err, presId);
      output(result);
      process.exit(exitCode(result));
    }
  });

// ── Create commands ──

const create = program.command("create").description("Create new presentations");

create
  .command("from-template")
  .description("Create a new presentation by copying a template")
  .requiredOption("--template <id>", "Template presentation ID or URL")
  .requiredOption("--title <name>", "Title for the new presentation")
  .option("--folder <id>", "Target Google Drive folder ID")
  .action(async (opts) => {
    const cmd = "create from-template";
    const templateId = resolvePresentation(cmd, opts.template);
    if (!templateId) return process.exit(10);
    const clients = await getSlides(cmd);
    if (!clients) return process.exit(20);

    try {
      const result = await copyPresentation(
        clients.drive,
        templateId,
        opts.title,
        opts.folder
      );
      output(
        success(cmd, {
          presentationId: result.id,
          title: opts.title,
          url: result.url,
          template: templateId,
        })
      );
      process.exit(0);
    } catch (err) {
      const res = handleApiError(cmd, err, templateId);
      output(res);
      process.exit(exitCode(res));
    }
  });

// ── Edit commands ──

const edit = program.command("edit").description("Edit presentation content");

edit
  .command("replace-text")
  .description("Replace placeholder text across entire presentation")
  .requiredOption("--presentation <id>", "Presentation ID or URL")
  .requiredOption(
    "--replacements <json>",
    'JSON array of {placeholder, value} objects'
  )
  .action(async (opts) => {
    const cmd = "edit replace-text";
    const presId = resolvePresentation(cmd, opts.presentation);
    if (!presId) return process.exit(10);
    const clients = await getSlides(cmd);
    if (!clients) return process.exit(20);

    let replacements: SlideReplacement[];
    try {
      replacements = JSON.parse(opts.replacements);
      if (!Array.isArray(replacements)) throw new Error("Must be array");
      // Unescape \n and \t in replacement values
      replacements = replacements.map((r) => ({
        ...r,
        value: unescapeText(r.value),
      }));
    } catch {
      output(
        error(cmd, "VALIDATION_ERROR", "Invalid JSON for --replacements")
      );
      return process.exit(10);
    }

    try {
      const result = await replaceAllText(clients.slides, presId, replacements);
      output(success(cmd, result, { presentationId: presId }));
      process.exit(0);
    } catch (err) {
      const result = handleApiError(cmd, err, presId);
      output(result);
      process.exit(exitCode(result));
    }
  });

edit
  .command("set-text")
  .description("Clear and set text on a specific element")
  .requiredOption("--presentation <id>", "Presentation ID or URL")
  .requiredOption("--object-id <id>", "Element object ID")
  .requiredOption("--text <text>", "New text content")
  .action(async (opts) => {
    const cmd = "edit set-text";
    const presId = resolvePresentation(cmd, opts.presentation);
    if (!presId) return process.exit(10);
    const clients = await getSlides(cmd);
    if (!clients) return process.exit(20);

    const text = unescapeText(opts.text);
    try {
      await clearAndSetText(clients.slides, presId, opts.objectId, text);
      output(
        success(cmd, { objectId: opts.objectId, text }, { presentationId: presId })
      );
      process.exit(0);
    } catch (err) {
      const result = handleApiError(cmd, err, presId);
      output(result);
      process.exit(exitCode(result));
    }
  });

edit
  .command("delete-slide")
  .description("Delete a slide by object ID")
  .requiredOption("--presentation <id>", "Presentation ID or URL")
  .requiredOption("--slide-id <id>", "Slide object ID to delete")
  .action(async (opts) => {
    const cmd = "edit delete-slide";
    const presId = resolvePresentation(cmd, opts.presentation);
    if (!presId) return process.exit(10);
    const clients = await getSlides(cmd);
    if (!clients) return process.exit(20);

    try {
      await deleteSlide(clients.slides, presId, opts.slideId);
      output(
        success(cmd, { deleted: opts.slideId }, { presentationId: presId })
      );
      process.exit(0);
    } catch (err) {
      const result = handleApiError(cmd, err, presId);
      output(result);
      process.exit(exitCode(result));
    }
  });

edit
  .command("delete-slides")
  .description("Delete multiple slides by object IDs")
  .requiredOption("--presentation <id>", "Presentation ID or URL")
  .requiredOption("--slide-ids <json>", "JSON array of slide object IDs")
  .action(async (opts) => {
    const cmd = "edit delete-slides";
    const presId = resolvePresentation(cmd, opts.presentation);
    if (!presId) return process.exit(10);
    const clients = await getSlides(cmd);
    if (!clients) return process.exit(20);

    let slideIds: string[];
    try {
      slideIds = JSON.parse(opts.slideIds);
      if (!Array.isArray(slideIds)) throw new Error("Must be array");
    } catch {
      output(error(cmd, "VALIDATION_ERROR", "Invalid JSON for --slide-ids"));
      return process.exit(10);
    }

    try {
      const result = await deleteSlides(clients.slides, presId, slideIds);
      output(success(cmd, result, { presentationId: presId }));
      process.exit(0);
    } catch (err) {
      const result = handleApiError(cmd, err, presId);
      output(result);
      process.exit(exitCode(result));
    }
  });

edit
  .command("duplicate-slide")
  .description("Duplicate a slide")
  .requiredOption("--presentation <id>", "Presentation ID or URL")
  .requiredOption("--slide-id <id>", "Slide object ID to duplicate")
  .option("--position <n>", "Target position (0-based index)")
  .action(async (opts) => {
    const cmd = "edit duplicate-slide";
    const presId = resolvePresentation(cmd, opts.presentation);
    if (!presId) return process.exit(10);
    const clients = await getSlides(cmd);
    if (!clients) return process.exit(20);

    const position = opts.position
      ? Number.parseInt(opts.position, 10)
      : undefined;

    try {
      const result = await duplicateSlide(
        clients.slides,
        presId,
        opts.slideId,
        position
      );
      output(success(cmd, result, { presentationId: presId }));
      process.exit(0);
    } catch (err) {
      const result = handleApiError(cmd, err, presId);
      output(result);
      process.exit(exitCode(result));
    }
  });

edit
  .command("batch")
  .description("Execute a batch of Slides API requests")
  .requiredOption("--presentation <id>", "Presentation ID or URL")
  .requiredOption("--requests <json>", "JSON array of Slides API request objects")
  .action(async (opts) => {
    const cmd = "edit batch";
    const presId = resolvePresentation(cmd, opts.presentation);
    if (!presId) return process.exit(10);
    const clients = await getSlides(cmd);
    if (!clients) return process.exit(20);

    let requests: unknown[];
    try {
      requests = JSON.parse(opts.requests);
      if (!Array.isArray(requests)) throw new Error("Must be array");
    } catch {
      output(error(cmd, "VALIDATION_ERROR", "Invalid JSON for --requests"));
      return process.exit(10);
    }

    try {
      const result = await batchUpdate(clients.slides, presId, requests);
      output(success(cmd, result, { presentationId: presId }));
      process.exit(0);
    } catch (err) {
      const result = handleApiError(cmd, err, presId);
      output(result);
      process.exit(exitCode(result));
    }
  });

edit
  .command("reorder-slides")
  .description("Move slides to a new position in the deck")
  .requiredOption("--presentation <id>", "Presentation ID or URL")
  .requiredOption("--slide-ids <json>", "JSON array of slide object IDs to move")
  .requiredOption("--position <n>", "Target position (0-based index)")
  .action(async (opts) => {
    const cmd = "edit reorder-slides";
    const presId = resolvePresentation(cmd, opts.presentation);
    if (!presId) return process.exit(10);
    const clients = await getSlides(cmd);
    if (!clients) return process.exit(20);

    let slideIds: string[];
    try {
      slideIds = JSON.parse(opts.slideIds);
      if (!Array.isArray(slideIds)) throw new Error("Must be array");
    } catch {
      output(error(cmd, "VALIDATION_ERROR", "Invalid JSON for --slide-ids"));
      return process.exit(10);
    }

    const position = Number.parseInt(opts.position, 10);
    if (!Number.isFinite(position) || position < 0) {
      output(error(cmd, "VALIDATION_ERROR", "Invalid position"));
      return process.exit(10);
    }

    try {
      const result = await reorderSlides(clients.slides, presId, slideIds, position);
      output(success(cmd, result, { presentationId: presId }));
      process.exit(0);
    } catch (err) {
      const result = handleApiError(cmd, err, presId);
      output(result);
      process.exit(exitCode(result));
    }
  });

edit
  .command("delete-element")
  .description("Delete a page element by object ID")
  .requiredOption("--presentation <id>", "Presentation ID or URL")
  .requiredOption("--object-id <id>", "Element object ID to delete")
  .action(async (opts) => {
    const cmd = "edit delete-element";
    const presId = resolvePresentation(cmd, opts.presentation);
    if (!presId) return process.exit(10);
    const clients = await getSlides(cmd);
    if (!clients) return process.exit(20);

    try {
      await deleteElement(clients.slides, presId, opts.objectId);
      output(
        success(cmd, { deleted: opts.objectId }, { presentationId: presId })
      );
      process.exit(0);
    } catch (err) {
      const result = handleApiError(cmd, err, presId);
      output(result);
      process.exit(exitCode(result));
    }
  });

edit
  .command("set-speaker-notes")
  .description("Set speaker notes on a slide")
  .requiredOption("--presentation <id>", "Presentation ID or URL")
  .requiredOption("--slide-id <id>", "Slide object ID")
  .requiredOption("--text <text>", "Speaker notes text")
  .action(async (opts) => {
    const cmd = "edit set-speaker-notes";
    const presId = resolvePresentation(cmd, opts.presentation);
    if (!presId) return process.exit(10);
    const clients = await getSlides(cmd);
    if (!clients) return process.exit(20);

    const text = unescapeText(opts.text);
    try {
      await setSpeakerNotes(clients.slides, presId, opts.slideId, text);
      output(
        success(cmd, { slideId: opts.slideId, text }, { presentationId: presId })
      );
      process.exit(0);
    } catch (err) {
      const result = handleApiError(cmd, err, presId);
      output(result);
      process.exit(exitCode(result));
    }
  });

edit
  .command("insert-image")
  .description("Replace an image placeholder with a new image from URL")
  .requiredOption("--presentation <id>", "Presentation ID or URL")
  .requiredOption("--object-id <id>", "Image element object ID")
  .requiredOption("--url <url>", "Public image URL (must be HTTPS)")
  .option("--method <method>", "Replace method: CENTER_INSIDE or CENTER_CROP", "CENTER_INSIDE")
  .action(async (opts) => {
    const cmd = "edit insert-image";
    const presId = resolvePresentation(cmd, opts.presentation);
    if (!presId) return process.exit(10);
    const clients = await getSlides(cmd);
    if (!clients) return process.exit(20);

    const method = opts.method as "CENTER_INSIDE" | "CENTER_CROP";
    try {
      await insertImage(clients.slides, presId, opts.objectId, opts.url, method);
      output(
        success(cmd, { objectId: opts.objectId, url: opts.url, method }, { presentationId: presId })
      );
      process.exit(0);
    } catch (err) {
      const result = handleApiError(cmd, err, presId);
      output(result);
      process.exit(exitCode(result));
    }
  });

edit
  .command("update-element")
  .description("Move or resize a page element by object ID")
  .requiredOption("--presentation <id>", "Presentation ID or URL")
  .requiredOption("--object-id <id>", "Element object ID")
  .option("--x <emu>", "New X position in EMU")
  .option("--y <emu>", "New Y position in EMU")
  .option("--width <emu>", "New width in EMU")
  .option("--height <emu>", "New height in EMU")
  .option("--scale-x <factor>", "Scale factor for width")
  .option("--scale-y <factor>", "Scale factor for height")
  .action(async (opts) => {
    const cmd = "edit update-element";
    const presId = resolvePresentation(cmd, opts.presentation);
    if (!presId) return process.exit(10);
    const clients = await getSlides(cmd);
    if (!clients) return process.exit(20);

    const transform: {
      x?: number;
      y?: number;
      width?: number;
      height?: number;
      scaleX?: number;
      scaleY?: number;
    } = {};

    if (opts.x !== undefined) transform.x = Number.parseFloat(opts.x);
    if (opts.y !== undefined) transform.y = Number.parseFloat(opts.y);
    if (opts.width !== undefined) transform.width = Number.parseFloat(opts.width);
    if (opts.height !== undefined) transform.height = Number.parseFloat(opts.height);
    if (opts.scaleX !== undefined) transform.scaleX = Number.parseFloat(opts.scaleX);
    if (opts.scaleY !== undefined) transform.scaleY = Number.parseFloat(opts.scaleY);

    try {
      await updateElementTransform(clients.slides, presId, opts.objectId, transform);
      output(
        success(cmd, { objectId: opts.objectId, transform }, { presentationId: presId })
      );
      process.exit(0);
    } catch (err) {
      const result = handleApiError(cmd, err, presId);
      output(result);
      process.exit(exitCode(result));
    }
  });

edit
  .command("update-text-style")
  .description("Update text styling (font, size, color, bold, italic) on a text element")
  .requiredOption("--presentation <id>", "Presentation ID or URL")
  .requiredOption("--object-id <id>", "Text element object ID")
  .option("--font <name>", "Font family name (e.g., Inter)")
  .option("--size <pt>", "Font size in points")
  .option("--bold <bool>", "Bold (true/false)")
  .option("--italic <bool>", "Italic (true/false)")
  .option("--underline <bool>", "Underline (true/false)")
  .option("--color <hex>", "Text foreground color (hex, e.g., #242e30)")
  .option("--bg-color <hex>", "Text background color (hex, e.g., #ff8000)")
  .option("--start <n>", "Start index of text range (0-based)")
  .option("--end <n>", "End index of text range")
  .action(async (opts) => {
    const cmd = "edit update-text-style";
    const presId = resolvePresentation(cmd, opts.presentation);
    if (!presId) return process.exit(10);
    const clients = await getSlides(cmd);
    if (!clients) return process.exit(20);

    const style: {
      fontFamily?: string;
      fontSize?: number;
      bold?: boolean;
      italic?: boolean;
      underline?: boolean;
      foregroundColor?: string;
      backgroundColor?: string;
    } = {};

    if (opts.font !== undefined) style.fontFamily = opts.font;
    if (opts.size !== undefined) style.fontSize = Number.parseFloat(opts.size);
    if (opts.bold !== undefined) style.bold = opts.bold === "true";
    if (opts.italic !== undefined) style.italic = opts.italic === "true";
    if (opts.underline !== undefined) style.underline = opts.underline === "true";
    if (opts.color !== undefined) style.foregroundColor = opts.color;
    if (opts.bgColor !== undefined) style.backgroundColor = opts.bgColor;

    const range =
      opts.start !== undefined || opts.end !== undefined
        ? {
            startIndex: opts.start ? Number.parseInt(opts.start, 10) : 0,
            endIndex: opts.end ? Number.parseInt(opts.end, 10) : undefined,
          }
        : undefined;

    try {
      await updateTextStyle(clients.slides, presId, opts.objectId, style, range);
      output(
        success(cmd, { objectId: opts.objectId, style, range }, { presentationId: presId })
      );
      process.exit(0);
    } catch (err) {
      const result = handleApiError(cmd, err, presId);
      output(result);
      process.exit(exitCode(result));
    }
  });

// ── Share commands ──

const share = program.command("share").description("Share presentations");

share
  .command("user")
  .description("Share with a specific user")
  .requiredOption("--presentation <id>", "Presentation ID or URL")
  .requiredOption("--email <email>", "User email address")
  .option("--role <role>", "Permission role: reader, writer, commenter", "reader")
  .action(async (opts) => {
    const cmd = "share user";
    const presId = resolvePresentation(cmd, opts.presentation);
    if (!presId) return process.exit(10);
    const clients = await getSlides(cmd);
    if (!clients) return process.exit(20);

    try {
      await sharePresentation(clients.drive, presId, opts.email, opts.role);
      output(
        success(
          cmd,
          { email: opts.email, role: opts.role },
          { presentationId: presId }
        )
      );
      process.exit(0);
    } catch (err) {
      const result = handleApiError(cmd, err, presId);
      output(result);
      process.exit(exitCode(result));
    }
  });

share
  .command("domain")
  .description("Share with entire domain")
  .requiredOption("--presentation <id>", "Presentation ID or URL")
  .requiredOption("--domain <domain>", "Domain name")
  .option("--role <role>", "Permission role: reader, writer, commenter", "reader")
  .action(async (opts) => {
    const cmd = "share domain";
    const presId = resolvePresentation(cmd, opts.presentation);
    if (!presId) return process.exit(10);
    const clients = await getSlides(cmd);
    if (!clients) return process.exit(20);

    try {
      await sharePresentationWithDomain(clients.drive, presId, opts.domain, opts.role);
      output(
        success(
          cmd,
          { domain: opts.domain, role: opts.role },
          { presentationId: presId }
        )
      );
      process.exit(0);
    } catch (err) {
      const result = handleApiError(cmd, err, presId);
      output(result);
      process.exit(exitCode(result));
    }
  });

// ── Move command ──

program
  .command("move")
  .description("Move presentation to a Drive folder")
  .requiredOption("--presentation <id>", "Presentation ID or URL")
  .requiredOption("--folder <id>", "Target folder ID")
  .action(async (opts) => {
    const cmd = "move";
    const presId = resolvePresentation(cmd, opts.presentation);
    if (!presId) return process.exit(10);
    const clients = await getSlides(cmd);
    if (!clients) return process.exit(20);

    try {
      await moveToFolder(clients.drive, presId, opts.folder);
      output(
        success(
          cmd,
          { moved: true, folder: opts.folder },
          { presentationId: presId }
        )
      );
      process.exit(0);
    } catch (err) {
      const result = handleApiError(cmd, err, presId);
      output(result);
      process.exit(exitCode(result));
    }
  });

// ── Export commands ──

const exportCmd = program.command("export").description("Export presentation data");

exportCmd
  .command("thumbnails")
  .description("Export slide thumbnails as PNG images")
  .requiredOption("--presentation <id>", "Presentation ID or URL")
  .option("--output <dir>", "Output directory", "/tmp/slides-export")
  .option("--slides <json>", "JSON array of slide indices to export (default: all)")
  .action(async (opts) => {
    const cmd = "export thumbnails";
    const presId = resolvePresentation(cmd, opts.presentation);
    if (!presId) return process.exit(10);
    const clients = await getSlides(cmd);
    if (!clients) return process.exit(20);

    let slideIndices: number[] | undefined;
    if (opts.slides) {
      try {
        slideIndices = JSON.parse(opts.slides);
        if (!Array.isArray(slideIndices)) throw new Error("Must be array");
      } catch {
        output(error(cmd, "VALIDATION_ERROR", "Invalid JSON for --slides"));
        return process.exit(10);
      }
    }

    try {
      const results = await getSlidesThumbnails(
        clients.slides,
        presId,
        opts.output,
        slideIndices
      );
      output(
        success(
          cmd,
          { outputDir: opts.output, exported: results.length, files: results },
          { presentationId: presId }
        )
      );
      process.exit(0);
    } catch (err) {
      const result = handleApiError(cmd, err, presId);
      output(result);
      process.exit(exitCode(result));
    }
  });

program.parse();
