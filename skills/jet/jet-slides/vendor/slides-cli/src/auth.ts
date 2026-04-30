import * as os from "node:os";
import * as path from "node:path";
import type { OAuth2Client } from "google-auth-library";
import { google } from "googleapis";

const SCOPES = [
  "https://www.googleapis.com/auth/presentations",
  "https://www.googleapis.com/auth/drive",
];

// Reuse sheets-cli token if available, otherwise use own token store
const SHEETS_TOKEN_PATH = path.join(
  os.homedir() || process.env.HOME || ".",
  ".sheets-cli",
  "token.json"
);
const SHEETS_CRED_PATH = path.join(
  os.homedir() || process.env.HOME || ".",
  ".sheets-cli",
  "credentials.json"
);
const DEFAULT_TOKEN_PATH = path.join(
  os.homedir() || process.env.HOME || ".",
  ".slides-cli",
  "token.json"
);
const LOOPBACK_PORT = 3848; // Different port from sheets-cli (3847)
const AUTH_TIMEOUT_MS = 5 * 60 * 1000;

export type AuthConfig = {
  credentialsPath: string;
  tokenPath?: string;
};

export async function getAuthClient(
  tokenPath?: string
): Promise<OAuth2Client | null> {
  // Try slides-cli token first, then fall back to sheets-cli token
  const pathsToTry = tokenPath
    ? [tokenPath]
    : [DEFAULT_TOKEN_PATH, SHEETS_TOKEN_PATH];

  for (const tp of pathsToTry) {
    try {
      const tokenFile = Bun.file(tp);
      if (!(await tokenFile.exists())) {
        continue;
      }

      const token = await tokenFile.json();

      // Find credentials file - check slides-cli dir, then sheets-cli dir
      const credPaths = [
        process.env.GF_SLIDES_CREDENTIALS,
        path.join(path.dirname(tp), "credentials.json"),
        SHEETS_CRED_PATH,
      ].filter(Boolean) as string[];

      let credentials: Record<string, unknown> | null = null;
      for (const cp of credPaths) {
        const credFile = Bun.file(cp);
        if (await credFile.exists()) {
          credentials = await credFile.json();
          break;
        }
      }

      if (!credentials) {
        continue;
      }

      const installed = credentials.installed as Record<string, unknown> | undefined;
      const web = credentials.web as Record<string, unknown> | undefined;
      const config = installed ?? web;
      if (!config) continue;

      const { client_id, client_secret, redirect_uris } = config as {
        client_id: string;
        client_secret: string;
        redirect_uris?: string[];
      };

      const oauth2Client = new google.auth.OAuth2(
        client_id,
        client_secret,
        redirect_uris?.[0] ?? "urn:ietf:wg:oauth:2.0:oob"
      );

      oauth2Client.setCredentials(token);
      return oauth2Client;
    } catch {
      continue;
    }
  }
  return null;
}

function waitForAuthCode(port: number, expectedState: string): Promise<string> {
  return new Promise((resolve, reject) => {
    let done = false;
    let server: ReturnType<typeof Bun.serve> | null = null;

    const timeout = setTimeout(() => {
      if (done) return;
      done = true;
      reject(new Error("OAuth timed out"));
      try {
        server?.stop();
      } catch {}
    }, AUTH_TIMEOUT_MS);

    server = Bun.serve({
      port,
      fetch(req) {
        const url = new URL(req.url);
        const code = url.searchParams.get("code");
        const error = url.searchParams.get("error");
        const state = url.searchParams.get("state");

        if (done) {
          return new Response("Done", { status: 200 });
        }

        const stopSoon = () => {
          setTimeout(() => {
            try {
              server?.stop();
            } catch {}
          }, 100);
        };

        if (error) {
          done = true;
          clearTimeout(timeout);
          stopSoon();
          reject(new Error(`OAuth error: ${error}`));
          return new Response(
            "<html><body><h1>Authentication failed</h1><p>You can close this window.</p></body></html>",
            { headers: { "Content-Type": "text/html" } }
          );
        }

        if (state !== expectedState) {
          done = true;
          clearTimeout(timeout);
          stopSoon();
          reject(new Error("OAuth state mismatch"));
          return new Response(
            "<html><body><h1>Authentication failed</h1><p>State mismatch. Close this window and retry.</p></body></html>",
            { headers: { "Content-Type": "text/html" } }
          );
        }

        if (code) {
          done = true;
          clearTimeout(timeout);
          stopSoon();
          resolve(code);
          return new Response(
            "<html><body><h1>Authentication successful!</h1><p>You can close this window and return to the terminal.</p></body></html>",
            { headers: { "Content-Type": "text/html" } }
          );
        }

        return new Response("Waiting for OAuth callback...", { status: 200 });
      },
    });
  });
}

export async function login(
  credentialsPath: string,
  tokenPath = DEFAULT_TOKEN_PATH
): Promise<{ success: boolean; message: string }> {
  try {
    const credFile = Bun.file(credentialsPath);
    if (!(await credFile.exists())) {
      return {
        success: false,
        message: `Credentials file not found: ${credentialsPath}`,
      };
    }

    const credentials = await credFile.json();
    const installed = credentials.installed as Record<string, unknown> | undefined;
    const web = credentials.web as Record<string, unknown> | undefined;
    const config = installed ?? web;
    if (!config) {
      return { success: false, message: "Invalid credentials file format" };
    }

    const { client_id, client_secret } = config as {
      client_id: string;
      client_secret: string;
    };

    const redirectUri = `http://localhost:${LOOPBACK_PORT}`;
    const oauth2Client = new google.auth.OAuth2(
      client_id,
      client_secret,
      redirectUri
    );

    const state = crypto.randomUUID();
    const authUrl = oauth2Client.generateAuthUrl({
      access_type: "offline",
      scope: SCOPES,
      state,
    });

    console.error("\nOpening browser for authentication...");
    console.error(`If browser doesn't open, visit:\n${authUrl}\n`);

    let openCmd = "xdg-open";
    if (process.platform === "darwin") {
      openCmd = "open";
    } else if (process.platform === "win32") {
      openCmd = "start";
    }
    Bun.$`${openCmd} ${authUrl}`.quiet().nothrow();

    const code = await waitForAuthCode(LOOPBACK_PORT, state);
    const { tokens } = await oauth2Client.getToken(code);

    const tokenDir = path.dirname(tokenPath);
    await Bun.$`mkdir -p ${tokenDir}`.quiet();

    // Copy credentials to config dir
    const configCredPath = path.join(tokenDir, "credentials.json");
    if (path.resolve(credentialsPath) !== path.resolve(configCredPath)) {
      await Bun.write(configCredPath, await credFile.text());
    }

    await Bun.write(tokenPath, JSON.stringify(tokens, null, 2));

    return { success: true, message: "Authentication successful" };
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    return { success: false, message: `Authentication failed: ${msg}` };
  }
}

export async function getAuthStatus(
  tokenPath = DEFAULT_TOKEN_PATH
): Promise<{ authenticated: boolean; tokenPath: string; usingSharedAuth: boolean }> {
  // Check slides-cli token
  const slidesClient = await getAuthClient(tokenPath);
  if (slidesClient) {
    return { authenticated: true, tokenPath, usingSharedAuth: false };
  }
  // Check sheets-cli token
  const sheetsClient = await getAuthClient(SHEETS_TOKEN_PATH);
  if (sheetsClient) {
    return { authenticated: true, tokenPath: SHEETS_TOKEN_PATH, usingSharedAuth: true };
  }
  return { authenticated: false, tokenPath, usingSharedAuth: false };
}

export async function logout(
  tokenPath = DEFAULT_TOKEN_PATH
): Promise<{ success: boolean; message: string }> {
  try {
    const tokenFile = Bun.file(tokenPath);
    if (await tokenFile.exists()) {
      await Bun.$`rm ${tokenPath}`.quiet();
      return { success: true, message: "Logged out successfully" };
    }
    return { success: true, message: "No active session" };
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    return { success: false, message: `Logout failed: ${msg}` };
  }
}
