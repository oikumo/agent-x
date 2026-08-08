from __future__ import annotations
import getpass
import os
import sys
import warnings

# Suppress upstream pydantic.v1 compatibility warning on Python 3.14+.
# This warning originates from langchain_core importing pydantic.v1 for
# backward compatibility — it is outside our control and adds noise to
# every agent invocation. The actual functionality is unaffected.
warnings.filterwarnings(
    "ignore",
    message=r"Core Pydantic V1 functionality isn't compatible with Python 3\.14",
    category=UserWarning,
)

from dotenv import load_dotenv

from agentx.ui.screens.main.main_controller import MainController
from agentx.ui.providers import ProviderRegistry

# ``override=True`` makes the ``.env`` file authoritative for secrets/config:
# ``python-dotenv`` by default does NOT overwrite an existing ``os.environ``
# value, so a stale shell export (e.g. a dead ``NVIDIA_API_KEY`` left over in
# ``~/.bashrc``) would silently mask the valid key written in this repo's
# ``.env`` — and ``ChatNVIDIA`` would then 403 with no actionable hint.
# Passing ``override=True`` means the ``.env`` value always wins, which is the
# intent of having a committed ``.env`` for credentials in the first place.
# (Also fixes the symmetric case at ``llama_cpp_factory.py:6``.)
load_dotenv(override=True)

if not os.getenv("OPENROUTER_API_KEY"):
    os.environ["OPENROUTER_API_KEY"] = getpass.getpass(
        "Enter your OpenRouter API key: "
    )

def show():
    import importlib.metadata
    version = importlib.metadata.version("agentx")
    print(f"agentx {version}")
    print()

def main():
    show()
    
    # Default UI is the console. Opt into the TUI with --tui.
    # --no-tui is kept as a recognized no-op for backwards compatibility.
    use_tui = "--tui" in sys.argv
    has_tty = sys.stdin.isatty() and sys.stdout.isatty()
    
    if use_tui:
        if not has_tty:
            print("⚠️  Warning: Not running in a proper terminal (TTY not detected).")
            print("   TUI keyboard/mouse input will not work correctly.")
            print("   Falling back to console mode...")
            print("   To use TUI, run directly in a terminal (not piped).")
            print()
            use_tui = False
    
    if use_tui:
        print("🎨 Starting modern TUI... (press 'q' to quit, 'h' for help)")
        print()
        ui_provider = ProviderRegistry.get_default()
    else:
        print("💻 Using console mode (default). Pass --tui for the TUI.")
        print()
        ui_provider = ProviderRegistry.get("console")
    
    # Initialize UI
    ui_provider.initialize()
    
    # Create controller with provider for sub-view creation
    main_controller = MainController(provider=ui_provider)
    
    # Create view via provider
    main_view = ui_provider.create_main_view(main_controller)
    
    # Replace controller's view
    main_controller.view = main_view
    
    # Start application
    try:
        main_view.show()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if use_tui:
            print("Falling back to console mode...")
            # Try console fallback
            console_provider = ProviderRegistry.get("console")
            console_view = console_provider.create_main_view(main_controller)
            main_controller.view = console_view
            console_view.show()
    finally:
        # Cleanup
        ui_provider.shutdown()


def start():
    main()

if __name__ == "__main__":
    main()