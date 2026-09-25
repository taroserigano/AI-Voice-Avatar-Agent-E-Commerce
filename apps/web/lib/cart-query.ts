"use client";

import type { CartOut } from "@ai-commerce/contracts";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { browserApi, errorMessage, goToSignIn } from "./api-browser";

export const CART_KEY = ["cart"] as const;

class ApiError extends Error {}

async function check<T>(result: { data?: T; error?: unknown; response: Response }): Promise<T> {
  if (result.response.status === 401) {
    goToSignIn();
    throw new ApiError("Signed out");
  }
  if (result.data === undefined) throw new ApiError(errorMessage(result.error));
  return result.data;
}

export function useCart(initialData?: CartOut) {
  return useQuery({
    queryKey: CART_KEY,
    queryFn: async () => check(await browserApi.GET("/v1/cart")),
    initialData,
  });
}

export function useSetCartItem() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: async (vars: { variantId: string; quantity: number }) =>
      check(
        await browserApi.PUT("/v1/cart/items", {
          body: { variant_id: vars.variantId, quantity: vars.quantity },
        }),
      ),
    onSuccess: (cart) => client.setQueryData(CART_KEY, cart),
  });
}

export function useRemoveCartItem() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: async (itemId: string) => {
      const result = await browserApi.DELETE("/v1/cart/items/{item_id}", {
        params: { path: { item_id: itemId } },
      });
      if (result.response.status === 401) goToSignIn();
      if (!result.response.ok) throw new ApiError(errorMessage(result.error));
    },
    onSuccess: () => client.invalidateQueries({ queryKey: CART_KEY }),
  });
}
