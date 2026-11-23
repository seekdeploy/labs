local langs = LazyVim.opts("nvim-treesitter").ensure_installed
local parsers = require("nvim-treesitter.parsers")
local out = {}
for _, l in ipairs(langs) do
  local p = parsers[l]
  local i = p and p.install_info or {}
  table.insert(out, { lang = l, url = i.url, revision = i.revision, branch = i.branch,
    location = i.location, generate = i.generate or false, queries = i.queries })
end
io.stdout:write(vim.json.encode(out) .. "\n")
