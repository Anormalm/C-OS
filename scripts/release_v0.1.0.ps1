param(
    [switch]$DryRun
)

$tag = "v0.1.0"
$notesFile = "docs/releases/v0.1.0.md"

if ($DryRun) {
    Write-Host "[DryRun] Would run:"
    Write-Host "git tag -a $tag -m `"C-OS $tag`""
    Write-Host "git push origin $tag"
    Write-Host "gh release create $tag --title `"C-OS $tag`" --notes-file $notesFile"
    exit 0
}

git tag -a $tag -m "C-OS $tag"
git push origin $tag
gh release create $tag --title "C-OS $tag" --notes-file $notesFile
