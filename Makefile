STATICCHECK_VERSION ?= v0.6.1

.PHONY: build verify link now test vet lint pytest clean

# House toolchain. The product bar is `make pytest`.
build:
	go build -o bin/agentctl ./tools/agentctl

verify:
	go run ./tools/agentctl verify

link:
	go run ./tools/agentctl link

now:
	go run ./tools/agentctl now

test:
	go test ./...

vet:
	go vet ./...

lint: vet
	@files=$$(gofmt -l tools); \
	if [ -n "$$files" ]; then echo "gofmt needed:"; echo "$$files"; exit 1; fi
	go run honnef.co/go/tools/cmd/staticcheck@$(STATICCHECK_VERSION) ./tools/...

pytest:
	python -m pytest tests/ -q

clean:
	rm -rf bin
