"""WebPhantom CLI - Browser Forensics Decoder."""

from __future__ import annotations

import json
from pathlib import Path

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from webphantom import __version__
from webphantom.browsers.chrome import ChromeParser
from webphantom.browsers.firefox import FirefoxParser
from webphantom.core.detector import detect_os, find_browser_profiles
from webphantom.core.models import BrowserType, ScanResult

console = Console()


def get_parser(browser: BrowserType, profile_path: Path) -> ChromeParser | FirefoxParser | None:
    """Get the appropriate parser for a browser type."""
    if browser in (BrowserType.CHROME, BrowserType.EDGE, BrowserType.BRAVE):
        return ChromeParser(profile_path)
    elif browser == BrowserType.FIREFOX:
        return FirefoxParser(profile_path)
    return None


@click.group()
@click.version_option(__version__, prog_name="WebPhantom")
def main() -> None:
    """WebPhantom - Browser Forensics Decoder

    Recover web activity from dead machines, even after history was cleared.
    """
    pass


@main.command()
@click.argument("target_path", type=click.Path(exists=True))
@click.option("--browser", "-b", type=click.Choice(["chrome", "firefox", "all"]), default="all")
@click.option("--output", "-o", type=click.Path(), help="Output file path")
@click.option(
    "--format", "-f", "output_format", type=click.Choice(["json", "text"]), default="text"
)

def scan(target_path: str, browser: str, output: str | None, output_format: str) -> None:
    """Scan a mounted disk image or directory for browser artifacts."""
    root = Path(target_path)

    console.print(f"\n[bold cyan]WebPhantom[/bold cyan] v{__version__}")
    console.print(f"[dim]Scanning: {root}[/dim]\n")

    result = ScanResult()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Detecting browser profiles...", total=None)
        profiles = find_browser_profiles(root)
        progress.update(task, description=f"Found {len(profiles)} profiles", completed=True)

        if not profiles:
            console.print("[yellow]No browser profiles found in the target path.[/yellow]")
            return

        task = progress.add_task("Parsing artifacts...", total=len(profiles))

        for profile in profiles:
            if browser != "all" and profile.browser.value != browser:
                continue

            progress.update(task, description=f"Parsing {profile.browser.value} - {profile.name}")

            parser = get_parser(profile.browser, profile.profile_path)
            if parser:
                artifacts = parser.parse_all()
                result.artifacts.extend(artifacts)
                if profile.browser not in result.browsers_found:
                    result.browsers_found.append(profile.browser)
                result.profiles_scanned += 1

            progress.advance(task)

    _display_results(result, output, output_format)


@main.command()
def detect() -> None:
    """Detect browser profiles on the current system."""
    console.print(f"\n[bold cyan]WebPhantom[/bold cyan] v{__version__}")
    console.print(f"[dim]OS: {detect_os()}[/dim]\n")

    profiles = find_browser_profiles()

    if not profiles:
        console.print("[yellow]No browser profiles found.[/yellow]")
        return

    table = Table(title="Detected Browser Profiles")
    table.add_column("Browser", style="cyan")
    table.add_column("Profile Name", style="green")
    table.add_column("Path", style="dim")
    table.add_column("History DB", style="yellow")

    for profile in profiles:
        history_db = profile.history_db
        table.add_row(
            profile.browser.value,
            profile.name,
            str(profile.profile_path),
            "✓" if history_db else "✗",
        )

    console.print(table)


@main.command()
@click.argument("db_path", type=click.Path(exists=True))
def walinfo(db_path: str) -> None:
    """Show information about a WAL file."""
    from webphantom.core.wal_recovery import WALRecovery

    db = Path(db_path)
    wal = WALRecovery(db)

    console.print(f"\n[bold cyan]WAL Info[/bold cyan]: {db}\n")

    if wal.has_wal:
        console.print("[green]✓ WAL file exists[/green]")
        header = wal.read_wal_header()
        if header:
            console.print(f"  Magic: {header.get('magic', 'unknown')}")
            console.print(f"  Page size: {header.get('page_size', 'unknown')}")
            console.print(f"  Checkpoint seq: {header.get('checkpoint_seq', 'unknown')}")
    else:
        console.print("[red]✗ No WAL file found[/red]")

    if wal.has_journal:
        console.print("[green]✓ Journal file exists[/green]")
    else:
        console.print("[red]✗ No journal file found[/red]")


@main.command()
@click.argument("db_path", type=click.Path(exists=True))
@click.argument("table_name")
def walrecovery(db_path: str, table_name: str) -> None:
    """Attempt to recover deleted rows from WAL file."""
    from webphantom.core.wal_recovery import WALRecovery

    db = Path(db_path)
    wal = WALRecovery(db)

    console.print(f"\n[bold cyan]WAL Recovery[/bold cyan]: {db} -> {table_name}\n")

    if not wal.has_wal:
        console.print("[red]No WAL file found. Nothing to recover.[/red]")
        return

    console.print("[yellow]Scanning WAL for recoverable data...[/yellow]")
    recovered = wal.recover_deleted_rows(table_name)

    if recovered:
        console.print(f"\n[green]Found {len(recovered)} potential recoverable entries:[/green]\n")
        for i, row in enumerate(recovered[:10], 1):
            console.print(f"  {i}. {json.dumps(row, indent=2, default=str)[:200]}")
    else:
        console.print("[dim]No recoverable data found in WAL.[/dim]")


def _display_results(result: ScanResult, output: str | None, output_format: str) -> None:
    """Display scan results."""
    console.print(f"\n{'='*60}")
    console.print("[bold]Scan Complete[/bold]")
    console.print(f"{'='*60}\n")

    console.print(f"Profiles scanned: {result.profiles_scanned}")
    console.print(f"Browsers found: {', '.join(b.value for b in result.browsers_found)}")
    console.print(f"Total artifacts: {result.total_artifacts}")
    console.print(f"WAL recovered: {result.wal_files_recovered}")

    if not result.artifacts:
        console.print("\n[yellow]No artifacts found.[/yellow]")
        return

    table = Table(title="Artifacts Found")
    table.add_column("Type", style="cyan")
    table.add_column("Browser", style="green")
    table.add_column("URL", style="white", max_width=50)
    table.add_column("Title", style="dim", max_width=30)
    table.add_column("WAL", style="yellow")

    for artifact in result.artifacts[:50]:
        table.add_row(
            artifact.artifact_type.value,
            artifact.browser.value,
            artifact.url[:50],
            artifact.title[:30] if artifact.title else "",
            "✓" if artifact.from_wal else "",
        )

    console.print(table)

    if output:
        _export_results(result, output, output_format)


def _export_results(result: ScanResult, output_path: str, output_format: str) -> None:
    """Export results to file."""
    path = Path(output_path)

    if output_format == "json":
        data = {
            "total_artifacts": result.total_artifacts,
            "browsers_found": [b.value for b in result.browsers_found],
            "profiles_scanned": result.profiles_scanned,
            "artifacts": [a.to_dict() for a in result.artifacts],
        }
        path.write_text(json.dumps(data, indent=2, default=str))
        console.print(f"\n[green]Exported to {path}[/green]")
    else:
        lines = []
        for artifact in result.artifacts:
            lines.append(
                f"[{artifact.timestamp}] {artifact.browser.value:10} "
                f"{artifact.artifact_type.value:10} {artifact.url}"
            )
        path.write_text("\n".join(lines))
        console.print(f"\n[green]Exported to {path}[/green]")


if __name__ == "__main__":
    main()
