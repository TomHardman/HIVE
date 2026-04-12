#!/usr/bin/env python3
"""
Utility script to delete saved model weights by prefix.
Useful for cleaning up old checkpoints.
"""

import argparse
import os
from pathlib import Path


def delete_models_by_prefix(prefix: str, model_dir: str = 'models/', dry_run: bool = False) -> None:
    """
    Delete all model files matching a given prefix.

    Args:
        prefix: Filename prefix to match (e.g., 'simplified_it')
        model_dir: Directory containing model files
        dry_run: If True, show what would be deleted without actually deleting
    """
    model_path = Path(model_dir)

    if not model_path.exists():
        print(f"Error: Model directory '{model_dir}' does not exist")
        return

    # Find all .pt files matching the prefix
    matching_files = list(model_path.glob(f'{prefix}*.pt'))

    if not matching_files:
        print(f"No model files found matching prefix '{prefix}' in '{model_dir}'")
        return

    print(f"Found {len(matching_files)} model file(s) matching prefix '{prefix}':")
    for f in sorted(matching_files):
        size_mb = f.stat().st_size / (1024 * 1024)
        print(f"  - {f.name} ({size_mb:.2f} MB)")

    if dry_run:
        print("\n[DRY RUN] No files were deleted.")
        return

    # Confirm deletion
    response = input(f"\nDelete these {len(matching_files)} file(s)? (y/N): ")
    if response.lower() != 'y':
        print("Cancelled.")
        return

    # Delete files
    deleted_count = 0
    for f in matching_files:
        try:
            f.unlink()
            deleted_count += 1
            print(f"  Deleted: {f.name}")
        except Exception as e:
            print(f"  Error deleting {f.name}: {e}")

    print(f"\nSuccessfully deleted {deleted_count}/{len(matching_files)} file(s)")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Delete saved model weights by prefix',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python delete_models.py simplified_it
  python delete_models.py --prefix dqn --dry-run
  python delete_models.py --prefix simplified --dir /path/to/models
        """
    )
    parser.add_argument('--prefix', type=str, required=True,
                        help="Prefix of model files to delete (e.g., 'simplified_it')")
    parser.add_argument('--dir', type=str, default='models/',
                        help="Directory containing model files (default: models/)")
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be deleted without actually deleting')
    args = parser.parse_args()

    delete_models_by_prefix(args.prefix, args.dir, dry_run=args.dry_run)
