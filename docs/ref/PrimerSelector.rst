PrimerSelector
~~~~~~~~~~~~~~~~

.. mermaid::

    graph TD

    ap[available_primers]
    cafl[compute_all_forbidden_locations]
    cavp[compute_all_valid_primers]
    ccp[compute_coverage_points]
    cfpl[compute_forbidden_patterns_locations]
    cnul[compute_non_unique_locations]
    csp[compute_sequence_primers]
    seq[sequence/record]
    sp[select_primers]
    trlr[tm_range, length_range]


    seq -->cnul
    cnul --> cafl
    seq -->cfpl
    cfpl --> cafl
    seq --> csp
    trlr --> csp
    csp -->cavp
    cafl--> cavp
    ap --> cavp
    cavp  -->sp
    ccp --> sp
    seq --> ccp

    style ap fill:#fff;
    style trlr fill:#fff;
    style seq fill:#fff;

.. autoclass:: lala.PrimerSelector
   :members:
