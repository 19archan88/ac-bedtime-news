#!/usr/bin/env python3
"""Official report entry point: require acknowledged onboarding before rendering."""
import argparse
from pathlib import Path
from build_report_html import build
from profile_store import require_ready


def prepare(source, archive=None, child_id=None, temporary=False, acknowledged=False, output=None, headline=None, audience='parent'):
    if temporary:
        if archive or not acknowledged:
            raise ValueError('Temporary mode requires explicit onboarding acknowledgement and no archive')
        return build(source, output, headline, audience)
    if not archive:
        raise ValueError('Choose a private archive or explicitly acknowledged temporary mode')
    _, selected = require_ready(archive, child_id)
    destination = Path(archive).expanduser().resolve() / 'children' / selected / 'reports'
    if output:
        raise ValueError('Persistent reports use the selected child archive; use temporary mode for custom output')
    return build(source, destination / Path(source).with_suffix('.html').name, headline, audience)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source')
    parser.add_argument('--archive')
    parser.add_argument('--child-id')
    parser.add_argument('--temporary', action='store_true')
    parser.add_argument('--onboarding-acknowledged', action='store_true')
    parser.add_argument('--output')
    parser.add_argument('--headline')
    parser.add_argument('--audience', choices=['parent', 'child'], default='parent')
    args = parser.parse_args()
    print(prepare(args.source, args.archive, args.child_id, args.temporary,
                  args.onboarding_acknowledged, args.output, args.headline, args.audience))


if __name__ == '__main__':
    main()
