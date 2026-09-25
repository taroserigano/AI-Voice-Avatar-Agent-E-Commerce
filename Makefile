# Thin wrappers around the pnpm scripts in package.json (which also work on Windows).
.PHONY: bootstrap infra-up infra-down dev test test-e2e lint typecheck reindex contracts eval-search

bootstrap:    ; pnpm bootstrap
infra-up:     ; pnpm infra:up
infra-down:   ; pnpm infra:down
dev:          ; pnpm dev
test:         ; pnpm test
test-e2e:     ; pnpm test:e2e
lint:         ; pnpm lint
typecheck:    ; pnpm typecheck
reindex:      ; pnpm reindex
contracts:    ; pnpm contracts
eval-search:  ; pnpm eval:search
