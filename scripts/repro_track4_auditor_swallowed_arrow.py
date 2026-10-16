#!/usr/bin/env python3
"""
Live Probe for Track 4: Auditor False-Positive ARROW_SWALLOWED bug.
Proves that auditor.py assumes label_position='auto' sits centered on line,
even though both pptx_compiler.py and svg_compiler.py offset vertical auto-labels by 35px to the side.
"""

from src.ppt_engine.diagram_v2.models import DiagramSpec, NodeSpec, FlowSpec
from src.ppt_engine.diagram_v2.auditor import DiagramAuditor

def main():
    print("=== Track 4: Live Probe on Auditor ARROW_SWALLOWED Rule ===")
    spec = DiagramSpec(
        id="test_vertical_flow",
        name="Test Vertical Flow",
        nodes=[
            NodeSpec(id="n1", title="Top Node", x=5.0, y=1.0, w=2.0, h=1.0),
            NodeSpec(id="n2", title="Bottom Node", x=5.0, y=2.7, w=2.0, h=1.0),
        ],
        flows=[
            FlowSpec(
                source="n1",
                target="n2",
                label="Parquet Ingest",
                label_position="auto", # Should resolve to "side"
                curve="straight"
            )
        ]
    )

    auditor = DiagramAuditor(spec)
    issues = auditor.audit()
    
    print(f"Auditor reported {len(issues)} issue(s):")
    for i in issues:
        print(f"  {i.format_line()}")
        
    has_swallowed = any(i.category == "ARROW_SWALLOWED" for i in issues)
    print(f"\nDefect Proven: ARROW_SWALLOWED is triggered on 'auto' label: {has_swallowed}")

if __name__ == "__main__":
    main()
