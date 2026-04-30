import type { OAuth2Client } from "google-auth-library";
import { google, type slides_v1, type drive_v3 } from "googleapis";
import type { PresentationInfo, SlideReplacement } from "./types";

export function getSlidesClient(auth: OAuth2Client): slides_v1.Slides {
  return google.slides({ version: "v1", auth });
}

export function getDriveClient(auth: OAuth2Client): drive_v3.Drive {
  return google.drive({ version: "v3", auth });
}

// ── Read operations ──

export async function getPresentation(
  slides: slides_v1.Slides,
  presentationId: string
): Promise<PresentationInfo> {
  const res = await slides.presentations.get({ presentationId });
  const pres = res.data;

  const slidePages = pres.slides ?? [];
  const parsedSlides = slidePages.map((slide) => {
    const textContent: string[] = [];
    for (const element of slide.pageElements ?? []) {
      if (element.shape?.text) {
        const text = element.shape.text.textElements
          ?.map((te) => te.textRun?.content ?? "")
          .join("")
          .trim();
        if (text) {
          textContent.push(text);
        }
      }
    }
    return {
      objectId: slide.objectId ?? "",
      layoutId: slide.slideProperties?.layoutObjectId ?? undefined,
      textContent,
    };
  });

  return {
    presentationId: pres.presentationId ?? presentationId,
    title: pres.title ?? "",
    url: `https://docs.google.com/presentation/d/${presentationId}/edit`,
    slideCount: slidePages.length,
    pageSize: {
      width: pres.pageSize?.width?.magnitude ?? 0,
      height: pres.pageSize?.height?.magnitude ?? 0,
    },
    slides: parsedSlides,
  };
}

interface ParsedElement {
  objectId: string;
  type: string;
  text?: string;
  position?: { x: number; y: number; width: number; height: number };
  children?: ParsedElement[];
}

function parsePageElement(el: slides_v1.Schema$PageElement): ParsedElement {
  const text = el.shape?.text?.textElements
    ?.map((te) => te.textRun?.content ?? "")
    .join("")
    .trim();

  const transform = el.transform;
  const size = el.size;

  const isGroup = !!(el as Record<string, unknown>).elementGroup;
  const type = el.shape ? "shape" : el.image ? "image" : el.table ? "table" : isGroup ? "group" : "other";

  // Extract autofit property from shape
  const autofit = el.shape?.shapeProperties?.autofit;
  const autofitType = autofit?.autofitType ?? undefined;

  // Extract first text run style
  const firstTextRun = el.shape?.text?.textElements?.find((te) => te.textRun?.content?.trim());
  const textStyle = firstTextRun?.textRun?.style;
  const fontInfo = textStyle ? {
    fontFamily: textStyle.weightedFontFamily?.fontFamily ?? textStyle.fontFamily ?? undefined,
    weight: textStyle.weightedFontFamily?.weight ?? undefined,
    bold: textStyle.bold ?? undefined,
    italic: textStyle.italic ?? undefined,
    fontSize: textStyle.fontSize?.magnitude ?? undefined,
    foregroundColor: textStyle.foregroundColor?.opaqueColor?.rgbColor ?? undefined,
  } : undefined;

  // Extract shape fill
  const shapeFill = el.shape?.shapeProperties?.shapeBackgroundFill?.solidFill?.color?.rgbColor;

  const parsed: ParsedElement = {
    objectId: el.objectId ?? "",
    type,
    text: text || undefined,
    position:
      transform && size
        ? {
            x: transform.translateX ?? 0,
            y: transform.translateY ?? 0,
            width: size.width?.magnitude ?? 0,
            height: size.height?.magnitude ?? 0,
            scaleX: transform.scaleX ?? undefined,
            scaleY: transform.scaleY ?? undefined,
          }
        : undefined,
    autofitType: autofitType ?? undefined,
    fontInfo: fontInfo ?? undefined,
    shapeFill: shapeFill ?? undefined,
  } as ParsedElement;

  // Recurse into group children
  if (isGroup) {
    const group = (el as Record<string, unknown>).elementGroup as { children?: slides_v1.Schema$PageElement[] };
    if (group.children && group.children.length > 0) {
      parsed.children = group.children.map(parsePageElement);
    }
  }

  return parsed;
}

export async function getSlide(
  slides: slides_v1.Slides,
  presentationId: string,
  slideIndex: number
): Promise<{
  objectId: string;
  elements: ParsedElement[];
}> {
  const res = await slides.presentations.get({ presentationId });
  const pres = res.data;
  const slidePages = pres.slides ?? [];

  if (slideIndex < 0 || slideIndex >= slidePages.length) {
    throw new Error(
      `Slide index ${slideIndex} out of range (0-${slidePages.length - 1})`
    );
  }

  const slide = slidePages[slideIndex]!;
  const elements = (slide.pageElements ?? []).map(parsePageElement);

  return { objectId: slide.objectId ?? "", elements };
}

export async function listLayouts(
  slides: slides_v1.Slides,
  presentationId: string
): Promise<
  Array<{
    objectId: string;
    layoutName: string;
    placeholders: Array<{
      objectId: string;
      type: string;
      index?: number;
    }>;
  }>
> {
  const res = await slides.presentations.get({ presentationId });
  const pres = res.data;
  const layouts = pres.layouts ?? [];

  return layouts.map((layout) => {
    const placeholders = (layout.pageElements ?? [])
      .filter((el) => el.shape?.placeholder)
      .map((el) => ({
        objectId: el.objectId ?? "",
        type: el.shape?.placeholder?.type ?? "NONE",
        index: el.shape?.placeholder?.index ?? undefined,
      }));

    return {
      objectId: layout.objectId ?? "",
      layoutName: layout.layoutProperties?.displayName ?? layout.layoutProperties?.name ?? "",
      placeholders,
    };
  });
}

export async function extractAllText(
  slides: slides_v1.Slides,
  presentationId: string
): Promise<
  Array<{
    slideIndex: number;
    objectId: string;
    texts: string[];
    speakerNotes?: string;
  }>
> {
  const res = await slides.presentations.get({ presentationId });
  const pres = res.data;
  const slidePages = pres.slides ?? [];

  return slidePages.map((slide, index) => {
    const texts: string[] = [];
    for (const element of slide.pageElements ?? []) {
      if (element.shape?.text) {
        const text = element.shape.text.textElements
          ?.map((te) => te.textRun?.content ?? "")
          .join("")
          .trim();
        if (text) {
          texts.push(text);
        }
      }
    }

    // Extract speaker notes
    let speakerNotes: string | undefined;
    const notesPage = slide.slideProperties?.notesPage;
    if (notesPage) {
      for (const element of notesPage.pageElements ?? []) {
        if (
          element.shape?.placeholder?.type === "BODY" &&
          element.shape?.text
        ) {
          speakerNotes = element.shape.text.textElements
            ?.map((te) => te.textRun?.content ?? "")
            .join("")
            .trim();
        }
      }
    }

    return {
      slideIndex: index,
      objectId: slide.objectId ?? "",
      texts,
      speakerNotes,
    };
  });
}

// ── Write operations ──

export async function copyPresentation(
  drive: drive_v3.Drive,
  sourceId: string,
  title: string,
  folderId?: string
): Promise<{ id: string; url: string }> {
  const requestBody: drive_v3.Schema$File = { name: title };
  if (folderId) {
    requestBody.parents = [folderId];
  }

  const res = await drive.files.copy({
    fileId: sourceId,
    requestBody,
    fields: "id, webViewLink",
  });

  const id = res.data.id!;
  return {
    id,
    url: res.data.webViewLink ?? `https://docs.google.com/presentation/d/${id}/edit`,
  };
}

export async function replaceAllText(
  slides: slides_v1.Slides,
  presentationId: string,
  replacements: SlideReplacement[]
): Promise<{ replacementsApplied: number }> {
  const requests: slides_v1.Schema$Request[] = replacements.map((r) => ({
    replaceAllText: {
      containsText: {
        text: r.placeholder,
        matchCase: true,
      },
      replaceText: r.value,
    },
  }));

  const res = await slides.presentations.batchUpdate({
    presentationId,
    requestBody: { requests },
  });

  return { replacementsApplied: res.data.replies?.length ?? 0 };
}

export async function deleteSlide(
  slides: slides_v1.Slides,
  presentationId: string,
  slideObjectId: string
): Promise<void> {
  await slides.presentations.batchUpdate({
    presentationId,
    requestBody: {
      requests: [{ deleteObject: { objectId: slideObjectId } }],
    },
  });
}

export async function deleteSlides(
  slides: slides_v1.Slides,
  presentationId: string,
  slideObjectIds: string[]
): Promise<{ deleted: number }> {
  if (slideObjectIds.length === 0) {
    return { deleted: 0 };
  }

  const requests: slides_v1.Schema$Request[] = slideObjectIds.map((id) => ({
    deleteObject: { objectId: id },
  }));

  await slides.presentations.batchUpdate({
    presentationId,
    requestBody: { requests },
  });

  return { deleted: slideObjectIds.length };
}

export async function duplicateSlide(
  slides: slides_v1.Slides,
  presentationId: string,
  slideObjectId: string,
  insertionIndex?: number
): Promise<{ newSlideId: string }> {
  const duplicateRequest: slides_v1.Schema$DuplicateObjectRequest = {
    objectId: slideObjectId,
  };

  const requests: slides_v1.Schema$Request[] = [
    { duplicateObject: duplicateRequest },
  ];

  const res = await slides.presentations.batchUpdate({
    presentationId,
    requestBody: { requests },
  });

  const reply = res.data.replies?.[0]?.duplicateObject;
  const newSlideId = reply?.objectId ?? "";

  // Move to target position if specified
  if (insertionIndex !== undefined && newSlideId) {
    await slides.presentations.batchUpdate({
      presentationId,
      requestBody: {
        requests: [
          {
            updateSlidesPosition: {
              slideObjectIds: [newSlideId],
              insertionIndex,
            },
          },
        ],
      },
    });
  }

  return { newSlideId };
}

export async function insertText(
  slides: slides_v1.Slides,
  presentationId: string,
  objectId: string,
  text: string,
  insertionIndex = 0
): Promise<void> {
  await slides.presentations.batchUpdate({
    presentationId,
    requestBody: {
      requests: [
        {
          insertText: {
            objectId,
            text,
            insertionIndex,
          },
        },
      ],
    },
  });
}

export async function clearAndSetText(
  slides: slides_v1.Slides,
  presentationId: string,
  objectId: string,
  text: string
): Promise<void> {
  // First delete all text, then insert new text
  // We need to get the current text length first
  const res = await slides.presentations.get({ presentationId });
  const pres = res.data;

  let textLength = 0;
  for (const slide of pres.slides ?? []) {
    for (const element of slide.pageElements ?? []) {
      if (element.objectId === objectId && element.shape?.text) {
        textLength =
          element.shape.text.textElements
            ?.map((te) => te.textRun?.content ?? "")
            .join("").length ?? 0;
        break;
      }
    }
  }

  const requests: slides_v1.Schema$Request[] = [];

  if (textLength > 0) {
    requests.push({
      deleteText: {
        objectId,
        textRange: {
          type: "ALL",
        },
      },
    });
  }

  requests.push({
    insertText: {
      objectId,
      text,
      insertionIndex: 0,
    },
  });

  await slides.presentations.batchUpdate({
    presentationId,
    requestBody: { requests },
  });
}

export async function batchUpdate(
  slides: slides_v1.Slides,
  presentationId: string,
  requests: slides_v1.Schema$Request[]
): Promise<{ repliesCount: number }> {
  const res = await slides.presentations.batchUpdate({
    presentationId,
    requestBody: { requests },
  });

  return { repliesCount: res.data.replies?.length ?? 0 };
}

export async function reorderSlides(
  slides: slides_v1.Slides,
  presentationId: string,
  slideObjectIds: string[],
  insertionIndex: number
): Promise<{ moved: number }> {
  if (slideObjectIds.length === 0) {
    return { moved: 0 };
  }

  await slides.presentations.batchUpdate({
    presentationId,
    requestBody: {
      requests: [
        {
          updateSlidesPosition: {
            slideObjectIds,
            insertionIndex,
          },
        },
      ],
    },
  });

  return { moved: slideObjectIds.length };
}

export async function deleteElement(
  slides: slides_v1.Slides,
  presentationId: string,
  objectId: string
): Promise<void> {
  await slides.presentations.batchUpdate({
    presentationId,
    requestBody: {
      requests: [{ deleteObject: { objectId } }],
    },
  });
}

export async function setSpeakerNotes(
  slides: slides_v1.Slides,
  presentationId: string,
  slideObjectId: string,
  notesText: string
): Promise<void> {
  // Get the presentation to find the notes page shape
  const res = await slides.presentations.get({ presentationId });
  const pres = res.data;

  let notesShapeId: string | undefined;
  for (const slide of pres.slides ?? []) {
    if (slide.objectId === slideObjectId) {
      const notesPage = slide.slideProperties?.notesPage;
      if (notesPage) {
        for (const element of notesPage.pageElements ?? []) {
          if (element.shape?.placeholder?.type === "BODY") {
            notesShapeId = element.objectId ?? undefined;
            break;
          }
        }
      }
      break;
    }
  }

  if (!notesShapeId) {
    throw new Error(`Could not find speaker notes shape for slide ${slideObjectId}`);
  }

  // Clear existing notes and set new text
  const requests: slides_v1.Schema$Request[] = [
    {
      deleteText: {
        objectId: notesShapeId,
        textRange: { type: "ALL" },
      },
    },
    {
      insertText: {
        objectId: notesShapeId,
        text: notesText,
        insertionIndex: 0,
      },
    },
  ];

  await slides.presentations.batchUpdate({
    presentationId,
    requestBody: { requests },
  });
}

export async function insertImage(
  slides: slides_v1.Slides,
  presentationId: string,
  objectId: string,
  imageUrl: string,
  replaceMethod: "CENTER_INSIDE" | "CENTER_CROP" = "CENTER_INSIDE"
): Promise<void> {
  await slides.presentations.batchUpdate({
    presentationId,
    requestBody: {
      requests: [
        {
          replaceImage: {
            imageObjectId: objectId,
            imageReplaceMethod: replaceMethod,
            url: imageUrl,
          },
        },
      ],
    },
  });
}

export async function getAllSlides(
  slides: slides_v1.Slides,
  presentationId: string
): Promise<
  Array<{
    slideIndex: number;
    objectId: string;
    elements: ParsedElement[];
  }>
> {
  const res = await slides.presentations.get({ presentationId });
  const pres = res.data;
  const slidePages = pres.slides ?? [];

  return slidePages.map((slide, index) => {
    const elements = (slide.pageElements ?? []).map(parsePageElement);

    return {
      slideIndex: index,
      objectId: slide.objectId ?? "",
      elements,
    };
  });
}

export async function getSlidesThumbnails(
  slides: slides_v1.Slides,
  presentationId: string,
  outputDir: string,
  slideIndices?: number[]
): Promise<Array<{ slideIndex: number; path: string }>> {
  const res = await slides.presentations.get({ presentationId });
  const pres = res.data;
  const slidePages = pres.slides ?? [];
  const results: Array<{ slideIndex: number; path: string }> = [];

  // Ensure output directory exists
  const fs = await import("fs");
  const path = await import("path");
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  const indicesToExport = slideIndices ?? slidePages.map((_, i) => i);

  for (const idx of indicesToExport) {
    if (idx < 0 || idx >= slidePages.length) continue;
    const slide = slidePages[idx]!;
    const slideId = slide.objectId!;

    const thumbRes = await slides.presentations.pages.getThumbnail({
      presentationId,
      pageObjectId: slideId,
      "thumbnailProperties.mimeType": "PNG",
      "thumbnailProperties.thumbnailSize": "LARGE",
    });

    const thumbUrl = thumbRes.data.contentUrl;
    if (!thumbUrl) continue;

    const response = await fetch(thumbUrl);
    const buffer = Buffer.from(await response.arrayBuffer());
    const filename = `slide-${String(idx).padStart(2, "0")}.png`;
    const filepath = path.join(outputDir, filename);
    fs.writeFileSync(filepath, buffer);
    results.push({ slideIndex: idx, path: filepath });
  }

  return results;
}

export async function updateElementTransform(
  slides: slides_v1.Slides,
  presentationId: string,
  objectId: string,
  transform: {
    x?: number;
    y?: number;
    width?: number;
    height?: number;
    scaleX?: number;
    scaleY?: number;
  }
): Promise<void> {
  const requests: slides_v1.Schema$Request[] = [];

  // If width or height is specified, update the size
  if (transform.width !== undefined || transform.height !== undefined) {
    const sizeFields: string[] = [];
    const size: slides_v1.Schema$Size = {};

    if (transform.width !== undefined) {
      size.width = { magnitude: transform.width, unit: "EMU" };
      sizeFields.push("width");
    }
    if (transform.height !== undefined) {
      size.height = { magnitude: transform.height, unit: "EMU" };
      sizeFields.push("height");
    }

    requests.push({
      updatePageElementTransform: {
        objectId,
        applyMode: "RELATIVE",
        transform: {
          scaleX: transform.scaleX ?? 1,
          scaleY: transform.scaleY ?? 1,
          translateX: 0,
          translateY: 0,
          unit: "EMU",
        },
      },
    });
  }

  // If x or y is specified, update the position via transform
  if (transform.x !== undefined || transform.y !== undefined) {
    // First get the current transform to compute a relative move
    const res = await slides.presentations.get({ presentationId });
    const pres = res.data;

    let currentTransform: slides_v1.Schema$AffineTransform | undefined;
    for (const slide of pres.slides ?? []) {
      for (const element of slide.pageElements ?? []) {
        if (element.objectId === objectId) {
          currentTransform = element.transform ?? undefined;
          break;
        }
      }
      if (currentTransform) break;
    }

    const newTransform: slides_v1.Schema$AffineTransform = {
      scaleX: currentTransform?.scaleX ?? 1,
      scaleY: currentTransform?.scaleY ?? 1,
      translateX: transform.x ?? currentTransform?.translateX ?? 0,
      translateY: transform.y ?? currentTransform?.translateY ?? 0,
      unit: "EMU",
    };

    requests.push({
      updatePageElementTransform: {
        objectId,
        applyMode: "ABSOLUTE",
        transform: newTransform,
      },
    });
  }

  if (requests.length > 0) {
    await slides.presentations.batchUpdate({
      presentationId,
      requestBody: { requests },
    });
  }
}

export async function updateTextStyle(
  slides: slides_v1.Slides,
  presentationId: string,
  objectId: string,
  style: {
    fontFamily?: string;
    fontSize?: number;
    bold?: boolean;
    italic?: boolean;
    underline?: boolean;
    foregroundColor?: string;
    backgroundColor?: string;
  },
  range?: { startIndex?: number; endIndex?: number }
): Promise<void> {
  const textStyle: slides_v1.Schema$TextStyle = {};
  const fields: string[] = [];

  if (style.fontFamily !== undefined) {
    textStyle.fontFamily = style.fontFamily;
    fields.push("fontFamily");
  }
  if (style.fontSize !== undefined) {
    textStyle.fontSize = { magnitude: style.fontSize, unit: "PT" };
    fields.push("fontSize");
  }
  if (style.bold !== undefined) {
    textStyle.bold = style.bold;
    fields.push("bold");
  }
  if (style.italic !== undefined) {
    textStyle.italic = style.italic;
    fields.push("italic");
  }
  if (style.underline !== undefined) {
    textStyle.underline = style.underline;
    fields.push("underline");
  }
  if (style.foregroundColor !== undefined) {
    const hex = style.foregroundColor.replace("#", "");
    const r = parseInt(hex.substring(0, 2), 16) / 255;
    const g = parseInt(hex.substring(2, 4), 16) / 255;
    const b = parseInt(hex.substring(4, 6), 16) / 255;
    textStyle.foregroundColor = {
      opaqueColor: { rgbColor: { red: r, green: g, blue: b } },
    };
    fields.push("foregroundColor");
  }
  if (style.backgroundColor !== undefined) {
    const hex = style.backgroundColor.replace("#", "");
    const r = parseInt(hex.substring(0, 2), 16) / 255;
    const g = parseInt(hex.substring(2, 4), 16) / 255;
    const b = parseInt(hex.substring(4, 6), 16) / 255;
    textStyle.backgroundColor = {
      opaqueColor: { rgbColor: { red: r, green: g, blue: b } },
    };
    fields.push("backgroundColor");
  }

  if (fields.length === 0) return;

  const textRange: slides_v1.Schema$Range = range
    ? {
        type: "FIXED_RANGE",
        startIndex: range.startIndex ?? 0,
        endIndex: range.endIndex,
      }
    : { type: "ALL" };

  await slides.presentations.batchUpdate({
    presentationId,
    requestBody: {
      requests: [
        {
          updateTextStyle: {
            objectId,
            style: textStyle,
            textRange: textRange,
            fields: fields.join(","),
          },
        },
      ],
    },
  });
}

// ── Drive operations ──

export async function findPresentations(
  drive: drive_v3.Drive,
  query: string,
  limit = 10
): Promise<
  Array<{
    id: string;
    name: string;
    url: string;
    modified: string;
  }>
> {
  const res = await drive.files.list({
    q: `mimeType='application/vnd.google-apps.presentation' and name contains '${query.replace(/'/g, "\\'")}'`,
    fields: "files(id, name, webViewLink, modifiedTime)",
    pageSize: limit,
    orderBy: "modifiedTime desc",
  });

  return (res.data.files ?? []).map((f) => ({
    id: f.id ?? "",
    name: f.name ?? "",
    url: f.webViewLink ?? "",
    modified: f.modifiedTime ?? "",
  }));
}

export async function moveToFolder(
  drive: drive_v3.Drive,
  fileId: string,
  folderId: string
): Promise<void> {
  // Get current parents
  const file = await drive.files.get({
    fileId,
    fields: "parents",
  });
  const previousParents = (file.data.parents ?? []).join(",");

  await drive.files.update({
    fileId,
    addParents: folderId,
    removeParents: previousParents,
    fields: "id, parents",
  });
}

export async function sharePresentation(
  drive: drive_v3.Drive,
  fileId: string,
  email: string,
  role: "reader" | "writer" | "commenter" = "reader"
): Promise<void> {
  await drive.permissions.create({
    fileId,
    requestBody: {
      type: "user",
      role,
      emailAddress: email,
    },
  });
}

export async function sharePresentationWithDomain(
  drive: drive_v3.Drive,
  fileId: string,
  domain: string,
  role: "reader" | "writer" | "commenter" = "reader"
): Promise<void> {
  await drive.permissions.create({
    fileId,
    requestBody: {
      type: "domain",
      role,
      domain,
    },
  });
}
