// Parse Google Slides URL to extract presentation ID
// Supports: https://docs.google.com/presentation/d/ID/edit#slide=id.xxx
const SLIDES_URL_REGEX = /\/presentation\/d\/([a-zA-Z0-9_-]+)/;

export function parsePresentationId(input: string): string {
  if (
    input.includes("docs.google.com") ||
    input.includes("/presentation/d/")
  ) {
    const match = input.match(SLIDES_URL_REGEX);
    if (match?.[1]) {
      return match[1];
    }
  }
  return input;
}

export type ErrorCode =
  | "VALIDATION_ERROR"
  | "AUTH_ERROR"
  | "PERMISSION_ERROR"
  | "API_ERROR";

export type SuccessResult<T = unknown> = {
  ok: true;
  cmd: string;
  presentationId?: string;
  result: T;
};

export type ErrorResult = {
  ok: false;
  cmd: string;
  error: {
    code: ErrorCode;
    message: string;
    details?: unknown;
  };
};

export type Result<T = unknown> = SuccessResult<T> | ErrorResult;

export type SlideLayout =
  | "TITLE"
  | "TITLE_AND_BODY"
  | "TITLE_AND_TWO_COLUMNS"
  | "TITLE_ONLY"
  | "SECTION_HEADER"
  | "BLANK";

export type SlideContent = {
  layout: SlideLayout;
  title?: string;
  subtitle?: string;
  body?: string;
  bodyLeft?: string;
  bodyRight?: string;
  speakerNotes?: string;
};

export type PresentationInfo = {
  presentationId: string;
  title: string;
  url: string;
  slideCount: number;
  pageSize: {
    width: number;
    height: number;
  };
  slides: Array<{
    objectId: string;
    layoutId?: string;
    textContent: string[];
  }>;
};

export type CreateFromTemplateOptions = {
  templateId: string;
  title: string;
  folderId?: string;
};

export type SlideReplacement = {
  placeholder: string;
  value: string;
};

export type BatchTextReplace = {
  replacements: SlideReplacement[];
};
