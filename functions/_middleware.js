// Redirect non-www to www canonical domain
export async function onRequest(context) {
  const url = new URL(context.request.url);

  // Redirect itvedas.com (non-www) to www.itvedas.com
  if (url.hostname === 'itvedas.com') {
    return Response.redirect(`https://www.itvedas.com${url.pathname}${url.search}`, 301);
  }

  return context.next();
}
