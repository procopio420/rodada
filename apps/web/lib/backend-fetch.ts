/** Preserve backend HTTP errors without automatically replaying JSON mutations. */
export function fetchBackend(input: string | URL, init: RequestInit = {}): Promise<Response> {
  if (typeof init.body !== "string") return fetch(input, init);

  // Undici retries HTTP 421 when a body has a replayable source. Its retry of a
  // consumed string body can throw UND_ERR_REQ_CONTENT_LENGTH_MISMATCH, hiding
  // the original tenant rejection. A stream has no replayable source: return
  // the original response and never retry this mutation (including on 307/308).
  const bytes = new TextEncoder().encode(init.body);
  const body = new ReadableStream<Uint8Array>({
    start(controller) {
      controller.enqueue(bytes);
      controller.close();
    },
  });
  // DRF treats a request without Content-Length as an empty stream, even when
  // ASGI received chunked bytes. Match the encoded bytes, never JS string length.
  const headers = new Headers(init.headers);
  headers.set("Content-Length", String(bytes.byteLength));
  const options: RequestInit & { duplex: "half" } = { ...init, headers, body, duplex: "half" };
  return fetch(input, options);
}
