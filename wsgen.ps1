# No param() block on purpose: a declared -Command/-Rest parameter set makes
# PowerShell try to bind flags like -o/-n/-c to its own parameters (or its
# common parameters) before they reach the wrapped script. Reading $args
# directly avoids that.

$Root = "C:\claude_code\WordsearchGenerator"

function Show-Usage {
    Write-Host "Usage: wsgen <page|book|bigbook|bigbook-acot|validate> [args...]"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  wsgen page data\input_page.json -o output\ --pdf"
    Write-Host "  wsgen book data\input_book.json output\"
    Write-Host "  wsgen bigbook data\books\01_animals_20_lists.json output\ -n mijn_boek -c 4 -d"
    Write-Host ""
    Write-Host "Input/output paths are relative to the folder you run wsgen from,"
    Write-Host "NOT relative to $Root."
}

if ($args.Count -eq 0) {
    Show-Usage
    exit 1
}

$Command = $args[0]
if ($args.Count -gt 1) {
    $Rest = $args[1..($args.Count - 1)]
} else {
    $Rest = @()
}

switch ($Command.ToLower()) {
    "page" { py -3 "$Root\scripts\generate_ws_page.py" @Rest; exit $LASTEXITCODE }
    "book" { py -3 "$Root\scripts\generate_ws_book.py" @Rest; exit $LASTEXITCODE }
    "bigbook" { py -3 "$Root\scripts\generate_big_ws_book.py" @Rest; exit $LASTEXITCODE }
    "bigbook-acot" { py -3 "$Root\scripts\generate_big_ws_book_ACOT.py" @Rest; exit $LASTEXITCODE }
    "validate" {
        $validatePath = "$Root\scripts\validate_books.py"
        if (Test-Path $validatePath) {
            py -3 $validatePath @Rest
            exit $LASTEXITCODE
        } else {
            Write-Host "validate_books.py is not present in $Root\scripts yet."
            exit 1
        }
    }
    default { Show-Usage; exit 1 }
}
