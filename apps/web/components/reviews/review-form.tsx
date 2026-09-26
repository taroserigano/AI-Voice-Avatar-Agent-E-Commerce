"use client";

import { LockIcon } from "@/components/icons";
import { Button } from "@/components/ui/button";
import { Field, Input, Textarea } from "@/components/ui/field";
import { Notice } from "@/components/ui/notice";
import { cn } from "@/lib/cn";
import {
  BODY_MAX,
  TITLE_MAX,
  validateReview,
  type ReviewDraft,
  type ReviewErrors,
} from "@/lib/reviews-query";
import type { ReviewIn } from "@ai-commerce/contracts";
import { useEffect, useId, useRef, useState, type FormEvent } from "react";
import { StarPicker } from "./star-picker";

function Counter({ length, max }: { length: number; max: number }) {
  const left = max - length;
  const near = left <= Math.max(10, Math.round(max * 0.1));
  return (
    <span className="flex items-center justify-between gap-3">
      <span>{max === TITLE_MAX ? "A short headline for your review." : "What did you like or dislike? How do you use it?"}</span>
      <span className={cn("shrink-0 tabular-nums", near ? "font-medium text-warning-700" : "text-muted")}>
        {length.toLocaleString("en-US")} / {max.toLocaleString("en-US")}
        <span className="sr-only"> characters used</span>
      </span>
    </span>
  );
}

/**
 * Write or edit the shopper's review. Focus moves to the star picker when the form opens and to
 * the first invalid control on a failed submit. `onSubmit` rejects with a message on API errors.
 */
export function ReviewForm({
  mode,
  productTitle,
  initial,
  pending,
  serverError,
  onSubmit,
  onCancel,
}: {
  mode: "create" | "edit";
  productTitle: string;
  initial: ReviewDraft;
  pending: boolean;
  serverError?: string;
  onSubmit: (review: ReviewIn) => void;
  onCancel: () => void;
}) {
  const uid = useId();
  const ids = { rating: `${uid}-rating`, title: `${uid}-title`, body: `${uid}-body`, heading: `${uid}-heading` };
  const [draft, setDraft] = useState<ReviewDraft>(initial);
  const [errors, setErrors] = useState<ReviewErrors>({});
  const starRef = useRef<HTMLInputElement>(null);
  const titleRef = useRef<HTMLInputElement>(null);
  const bodyRef = useRef<HTMLTextAreaElement>(null);
  const errorRef = useRef<HTMLDivElement>(null);

  // Opening the form puts focus on its first control (the star rating).
  useEffect(() => {
    starRef.current?.focus();
  }, []);

  // A server-side rejection is announced (role="alert") and takes focus so it isn't missed.
  useEffect(() => {
    if (serverError) errorRef.current?.focus();
  }, [serverError]);

  function submit(event: FormEvent) {
    event.preventDefault();
    if (pending) return;
    const result = validateReview(draft);
    if (!result.ok) {
      setErrors(result.errors);
      if (result.errors.rating) starRef.current?.focus();
      else if (result.errors.title) titleRef.current?.focus();
      else bodyRef.current?.focus();
      return;
    }
    setErrors({});
    onSubmit(result.value);
  }

  return (
    <form
      noValidate
      onSubmit={submit}
      aria-labelledby={ids.heading}
      className="animate-fade-up rounded-3xl border border-line bg-raised p-5 shadow-md sm:p-8"
    >
      <div className="flex flex-wrap items-start justify-between gap-x-6 gap-y-1">
        <div className="min-w-0">
          <h3 id={ids.heading} className="font-display text-xl font-semibold text-ink sm:text-2xl">
            {mode === "edit" ? "Edit your review" : "Write a review"}
          </h3>
          <p className="mt-1 line-clamp-1 text-sm text-muted">
            <span className="sr-only">Reviewing </span>
            {productTitle}
          </p>
        </div>
      </div>

      {serverError ? (
        <div ref={errorRef} tabIndex={-1} className="mt-5 rounded-xl outline-none focus-visible:outline-2 focus-visible:outline-offset-2">
          <Notice tone="error" title="We couldn't save your review">
            {serverError}
          </Notice>
        </div>
      ) : null}

      <div className="mt-6 space-y-6">
        <StarPicker
          name={ids.rating}
          value={draft.rating}
          onChange={(rating) => {
            setDraft((d) => ({ ...d, rating }));
            setErrors((e) => ({ ...e, rating: undefined }));
          }}
          error={errors.rating}
          firstInputRef={starRef}
          disabled={pending}
        />

        <Field
          id={ids.title}
          label="Title"
          optional
          hint={<Counter length={draft.title.length} max={TITLE_MAX} />}
          error={errors.title}
        >
          <Input
            ref={titleRef}
            id={ids.title}
            name="title"
            value={draft.title}
            maxLength={TITLE_MAX}
            autoComplete="off"
            placeholder="e.g. Comfortable for all-day wear"
            disabled={pending}
            onChange={(e) => setDraft((d) => ({ ...d, title: e.target.value }))}
            aria-describedby={errors.title ? `${ids.title}-hint ${ids.title}-error` : `${ids.title}-hint`}
            aria-invalid={errors.title ? true : undefined}
          />
        </Field>

        <Field
          id={ids.body}
          label="Review"
          optional
          hint={<Counter length={draft.body.length} max={BODY_MAX} />}
          error={errors.body}
        >
          <Textarea
            ref={bodyRef}
            id={ids.body}
            name="body"
            rows={5}
            value={draft.body}
            maxLength={BODY_MAX}
            disabled={pending}
            onChange={(e) => setDraft((d) => ({ ...d, body: e.target.value }))}
            aria-describedby={errors.body ? `${ids.body}-hint ${ids.body}-error` : `${ids.body}-hint`}
            aria-invalid={errors.body ? true : undefined}
            className="resize-y"
          />
        </Field>
      </div>

      <p className="mt-5 flex items-start gap-2 text-xs text-muted">
        <LockIcon className="mt-px size-3.5 shrink-0" />
        <span>
          Your review shows your first name and last initial. Please leave out personal details like
          addresses, phone numbers, or order numbers.
        </span>
      </p>

      <div className="mt-6 flex flex-col-reverse gap-3 border-t border-line pt-6 sm:flex-row sm:items-center sm:justify-end">
        <Button variant="ghost" onClick={onCancel} disabled={pending} className="sm:min-w-28">
          Cancel
        </Button>
        <Button type="submit" size="lg" loading={pending} className="sm:min-w-44">
          {pending ? "Posting…" : mode === "edit" ? "Save changes" : "Post review"}
        </Button>
      </div>
    </form>
  );
}
