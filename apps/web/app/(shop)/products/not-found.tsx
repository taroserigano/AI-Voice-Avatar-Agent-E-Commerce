// notFound() from products/[id]/layout.tsx is caught one segment up, here, so this reuses the
// product not-found UI (and its "Not found" title) rather than falling through to the site 404.
export { default, metadata } from "./[id]/not-found";
