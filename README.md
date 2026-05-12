# apidiff

A command-line utility to diff two OpenAPI spec files and highlight breaking vs non-breaking changes.

---

## Installation

```bash
pip install apidiff
```

Or install from source:

```bash
git clone https://github.com/yourname/apidiff.git
cd apidiff
pip install -e .
```

---

## Usage

```bash
apidiff old-spec.yaml new-spec.yaml
```

**Example output:**

```
✔ Non-breaking: Added new endpoint GET /users/{id}
✔ Non-breaking: Added optional query parameter ?limit to GET /users
✘ Breaking:     Removed endpoint DELETE /accounts/{id}
✘ Breaking:     Changed type of field `email` from string to integer in POST /users
```

### Options

| Flag | Description |
|------|-------------|
| `--format json` | Output results as JSON |
| `--breaking-only` | Show only breaking changes |
| `--exit-code` | Exit with code 1 if breaking changes are found |
| `--ignore-description` | Ignore changes to description fields |

```bash
apidiff old-spec.yaml new-spec.yaml --breaking-only --exit-code
```

---

## Supported Formats

- YAML (`.yaml`, `.yml`)
- JSON (`.json`)

---

## What Counts as a Breaking Change?

The following changes are considered **breaking**:

- Removing an existing endpoint
- Removing a required request parameter or field
- Changing the type of an existing field
- Making an optional parameter required
- Changing an existing success response status code

The following are considered **non-breaking**:

- Adding a new endpoint
- Adding an optional parameter
- Adding a new field to a response body
- Updating descriptions or documentation strings

---

## Contributing

Pull requests are welcome. Please open an issue first to discuss any significant changes.

---

## License

[MIT](LICENSE)
