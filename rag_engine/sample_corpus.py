"""A small built-in road/highway corpus so the engine runs with zero setup.
Topics intentionally span several themes (clearances, DPR, milestones, finance,
safety, drainage, land) so clustering has real structure to find."""

SAMPLE_DOCS = [
    {
        "source": "NH30_forest_clearance.txt",
        "text": (
            "Forest clearance for the NH-30 widening project was granted by the "
            "State Forest Department on 12 March 2024. Stage-I clearance covered "
            "18.4 hectares of forest land across sections 2 and 3. Compensatory "
            "afforestation of 36.8 hectares has been mandated as a condition. "
            "The net present value payment of Rs 2.1 crore was deposited prior to "
            "diversion of forest land."
        ),
    },
    {
        "source": "NH458_dpr_summary.txt",
        "text": (
            "The Detailed Project Report (DPR) for NH-458 covers a 42.5 km greenfield "
            "alignment with a four-lane configuration. The DPR estimates a total "
            "project cost of Rs 320 crore including land acquisition and utility "
            "shifting. Traffic surveys project an AADT of 18,500 vehicles by 2030. "
            "The DPR recommends two major bridges and seven minor culverts."
        ),
    },
    {
        "source": "project_milestones.txt",
        "text": (
            "Milestone-I requires 20 percent physical progress within 180 days of the "
            "appointed date. Milestone-II requires 35 percent of the project cost to "
            "be incurred by month 12. Milestone-III sets 75 percent completion at "
            "month 20. Failure to meet a milestone attracts damages as per the "
            "concession agreement."
        ),
    },
    {
        "source": "eot_policy.txt",
        "text": (
            "Extension of Time (EOT) may be granted for delays attributable to the "
            "authority, force majeure, or change of scope. The contractor must apply "
            "for EOT within 30 days of the delay event. For NH-30, an EOT of 56 days "
            "was approved owing to delayed forest clearance and monsoon disruption."
        ),
    },
    {
        "source": "land_acquisition.txt",
        "text": (
            "Land acquisition under the National Highways Act covers 3A notification, "
            "3D declaration and 3G award stages. For the Coastal Road project, 92 "
            "percent of required land has been acquired. Compensation disbursed to "
            "affected landowners totals Rs 47 crore. Pending parcels are under "
            "arbitration in two villages."
        ),
    },
    {
        "source": "road_safety_audit.txt",
        "text": (
            "The road safety audit flagged inadequate signage at three intersections "
            "and recommended crash barriers along a 4 km curved stretch. Pedestrian "
            "underpasses are advised near the school zone at chainage 12+400. Retro-"
            "reflective lane markings must comply with IRC:35 standards."
        ),
    },
    {
        "source": "drainage_design.txt",
        "text": (
            "Drainage design for section 2 includes RCC box culverts and lined side "
            "drains to handle a 25-year return-period storm. Cross drainage works "
            "comprise five pipe culverts of 1200 mm diameter. The longitudinal "
            "gradient was kept above 0.3 percent to ensure self-cleansing velocity."
        ),
    },
    {
        "source": "toll_revenue.txt",
        "text": (
            "Toll revenue on the operational NH-458 bypass averaged Rs 11.4 lakh per "
            "day in the last quarter. Commercial vehicles account for 62 percent of "
            "revenue. The user-fee plaza follows the closed tolling system with "
            "FASTag-only lanes. Annual revision is linked to the wholesale price index."
        ),
    },
    {
        "source": "financial_progress.txt",
        "text": (
            "Financial progress on the Ring Road Extension stands at 40 percent against "
            "a physical progress of 34 percent, indicating front-loaded mobilisation "
            "advances. The revised cost estimate increased by Rs 18 crore due to a "
            "change in pavement specification from bituminous to rigid concrete."
        ),
    },
    {
        "source": "pavement_spec.txt",
        "text": (
            "The pavement specification adopts a rigid concrete pavement with a 300 mm "
            "pavement quality concrete slab over a 150 mm dry lean concrete sub-base. "
            "Design life is 30 years for a cumulative traffic of 150 million standard "
            "axles. Joint spacing is 4.5 m with dowel bars at contraction joints."
        ),
    },
    {
        "source": "environment_clearance.txt",
        "text": (
            "Environmental clearance was obtained after a public hearing held in "
            "August 2023. The Environmental Impact Assessment identified noise "
            "barriers near two residential clusters and a green belt of native species "
            "along the right of way. Air quality monitoring is mandated quarterly "
            "during construction."
        ),
    },
    {
        "source": "quality_control.txt",
        "text": (
            "Quality control on embankment fill requires field density not less than "
            "95 percent of modified Proctor. Aggregate for the granular sub-base must "
            "meet the prescribed gradation and a CBR above 30 percent. Independent "
            "engineer approval is required before laying each pavement layer."
        ),
    },
]
