#!/usr/bin/env python3
"""View operation history from logs and manifests."""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

def load_manifests() -> List[Dict[str, Any]]:
    """Load all manifest files."""
    manifests_dir = Path("app/outputs/manifests")
    if not manifests_dir.exists():
        return []
    
    manifests = []
    for manifest_file in sorted(manifests_dir.glob("*.json"), reverse=True):
        try:
            with open(manifest_file) as f:
                data = json.load(f)
                data['_manifest_file'] = manifest_file.name
                manifests.append(data)
        except Exception as e:
            print(f"Warning: Could not load {manifest_file}: {e}")
    
    return manifests

def load_events(date: str = None) -> List[Dict[str, Any]]:
    """Load events from JSONL files."""
    logs_dir = Path("app/logs")
    if not logs_dir.exists():
        return []
    
    events = []
    
    # Determine which files to read
    if date:
        event_files = [logs_dir / f"events-{date}.jsonl"]
    else:
        # Read all event files
        event_files = sorted(logs_dir.glob("events-*.jsonl"), reverse=True)
        # Also try the symlink
        if (logs_dir / "events.jsonl").exists():
            event_files.insert(0, logs_dir / "events.jsonl")
    
    for event_file in event_files:
        if not event_file.exists():
            continue
        try:
            with open(event_file) as f:
                for line in f:
                    if line.strip():
                        events.append(json.loads(line))
        except Exception as e:
            print(f"Warning: Could not load {event_file}: {e}")
    
    return events

def format_timestamp(ts_str: str) -> str:
    """Format ISO timestamp to readable format."""
    try:
        dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return ts_str

def print_manifests_summary():
    """Print summary of all operations from manifests."""
    manifests = load_manifests()
    
    if not manifests:
        print("📁 No manifests found.")
        return
    
    print(f"\n📦 Operation History ({len(manifests)} operations)")
    print("=" * 80)
    
    for manifest in manifests[:20]:  # Latest 20
        op_id = manifest.get('op_id', 'N/A')
        mode = manifest.get('mode', 'N/A')
        status = manifest.get('status', 'N/A')
        written_at = manifest.get('written_at', 'N/A')
        workspace = manifest.get('workspace', 'N/A')
        project = manifest.get('project', 'N/A')
        version = manifest.get('target_version', 'N/A')
        
        status_icon = "✅" if status == "success" else "⚠️" if status == "partial_success" else "❌"
        
        print(f"\n{status_icon} [{format_timestamp(written_at)}] {op_id}")
        print(f"   Mode: {mode}")
        print(f"   Target: {workspace}/{project}/v{version}")
        print(f"   Status: {status}")
        
        if 'artifact' in manifest:
            artifact = manifest['artifact']
            print(f"   File: {artifact.get('filename', 'N/A')} ({artifact.get('size_bytes', 0) / 1024 / 1024:.2f} MB)")
        
        if 'api_response' in manifest:
            api_resp = manifest['api_response']
            if isinstance(api_resp, dict):
                if api_resp.get('status') == 'deployed':
                    print(f"   🚀 Deployed successfully!")
                elif 'error' in api_resp:
                    print(f"   ⚠️ Error: {api_resp.get('error', 'Unknown')[:60]}...")

def print_events_summary(limit: int = 50):
    """Print recent events."""
    events = load_events()
    
    if not events:
        print("📝 No events found.")
        return
    
    print(f"\n📝 Recent Events (showing {min(limit, len(events))} of {len(events)})")
    print("=" * 80)
    
    for event in events[:limit]:
        ts = event.get('ts', 'N/A')
        level = event.get('level', 'INFO')
        event_type = event.get('event', event.get('message', 'N/A'))
        
        level_icon = "🔴" if level == "ERROR" else "🟡" if level == "WARNING" else "🟢"
        
        print(f"{level_icon} [{format_timestamp(ts)}] {event_type}")
        
        # Print relevant details
        if 'workspace' in event:
            print(f"   Workspace: {event['workspace']}")
        if 'project' in event:
            print(f"   Project: {event['project']}")
        if 'count' in event:
            print(f"   Count: {event['count']}")

def print_stats():
    """Print statistics."""
    manifests = load_manifests()
    events = load_events()
    
    print(f"\n📊 Statistics")
    print("=" * 80)
    print(f"Total operations: {len(manifests)}")
    
    if manifests:
        success_count = sum(1 for m in manifests if m.get('status') == 'success')
        partial_count = sum(1 for m in manifests if m.get('status') == 'partial_success')
        failed_count = len(manifests) - success_count - partial_count
        
        print(f"  ✅ Successful: {success_count}")
        print(f"  ⚠️ Partial: {partial_count}")
        print(f"  ❌ Failed: {failed_count}")
    
    print(f"\nTotal events: {len(events)}")
    
    # Count by event type
    if events:
        event_types = {}
        for event in events:
            event_type = event.get('event', 'other')
            event_types[event_type] = event_types.get(event_type, 0) + 1
        
        print("\nTop events:")
        for event_type, count in sorted(event_types.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  • {event_type}: {count}")

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="View Roboflow Uploader operation history")
    parser.add_argument('--manifests', action='store_true', help='Show manifest summary')
    parser.add_argument('--events', action='store_true', help='Show events log')
    parser.add_argument('--stats', action='store_true', help='Show statistics')
    parser.add_argument('--limit', type=int, default=50, help='Limit number of items to show')
    parser.add_argument('--date', type=str, help='Filter by date (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    # If no specific option, show all
    show_all = not (args.manifests or args.events or args.stats)
    
    print(f"\n{'='*80}")
    print(f"🔍 Roboflow Uploader - Operation History")
    print(f"{'='*80}")
    
    if args.stats or show_all:
        print_stats()
    
    if args.manifests or show_all:
        print_manifests_summary()
    
    if args.events or show_all:
        print_events_summary(limit=args.limit)
    
    print(f"\n{'='*80}\n")

if __name__ == "__main__":
    main()

