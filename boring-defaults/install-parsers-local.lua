-- Second measurement only. Point each parser's install_info.path at a local git
-- checkout (see clone-parsers.sh), then run nvim-treesitter's normal install,
-- which compiles with `tree-sitter build` and installs parser + queries.
-- nvim-treesitter reloads its parser table during install and fires
-- `User TSUpdate`, so the override must live in that autocommand (README,
-- "Adding parsers"). Nothing in LazyVim's config is changed.
local src = vim.env.PARSER_SRC
local list = vim.json.decode(table.concat(vim.fn.readfile(vim.env.PARSERS_JSON), "\n"))
local function apply()
  local parsers = require("nvim-treesitter.parsers")
  for _, p in ipairs(list) do
    parsers[p.lang].install_info.path = src .. "/" .. vim.fs.basename(p.url) .. "-" .. p.revision
  end
end
vim.api.nvim_create_autocmd("User", { pattern = "TSUpdate", callback = apply })
apply()
local langs = vim.tbl_map(function(p) return p.lang end, list)
local ok = require("nvim-treesitter").install(langs, { summary = true }):wait(600000)
print("install returned", ok)
