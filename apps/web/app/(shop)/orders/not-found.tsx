// notFound() from orders/[id]/layout.tsx is caught one segment up, here, so this reuses the
// order not-found UI (and its "Order not found" title) rather than falling through to the site 404.
export { default, metadata } from "./[id]/not-found";
