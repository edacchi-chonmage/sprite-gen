// Python サーバー(http://100.103.94.8:4323)の /api/* へ中継する。
// trusted() が Host一致 + Origin無し(または一致)を要求するため、
// Origin ヘッダは転送しない(サーバー間通信としてリクエストする)。
const BACKEND_ORIGIN = "http://100.103.94.8:4323";

async function proxy(request: Request, path: string[]) {
  const search = new URL(request.url).search;
  const target = `${BACKEND_ORIGIN}/api/${path.join("/")}${search}`;

  const init: RequestInit = {
    method: request.method,
    headers: { "Content-Type": "application/json" },
  };
  if (request.method !== "GET" && request.method !== "HEAD") {
    init.body = await request.text();
  }

  const res = await fetch(target, init);
  const body = await res.text();
  return new Response(body, {
    status: res.status,
    headers: { "Content-Type": "application/json; charset=utf-8" },
  });
}

export async function GET(
  request: Request,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  return proxy(request, path);
}

export async function POST(
  request: Request,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  return proxy(request, path);
}
