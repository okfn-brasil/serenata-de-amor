module Documents.Fields exposing (isSearchable, labels, names, sets)


names : List String
names =
    [ "document_id"
    , "congressperson_name"
    , "congressperson_id"
    , "congressperson_document"
    , "term"
    , "state"
    , "party"
    , "term_id"
    , "subquota_number"
    , "subquota_description"
    , "subquota_group_id"
    , "subquota_group_description"
    , "supplier"
    , "cnpj_cpf"
    , "document_number"
    , "document_type"
    , "issue_date"
    , "document_value"
    , "remark_value"
    , "net_value"
    , "month"
    , "year"
    , "installment"
    , "passenger"
    , "leg_of_the_trip"
    , "batch_number"
    , "reimbursement_number"
    , "reimbursement_value"
    , "applicant_id"
    ]


labels : List String
labels =
    [ "Document ID"
    , "Congressperson name"
    , "Congressperson ID"
    , "Congressperson document"
    , "Term"
    , "State"
    , "Party"
    , "Term ID"
    , "Subquota number"
    , "Subquota description"
    , "Subquota group ID"
    , "Subquota group description"
    , "Supplier"
    , "CNPJ or CPF"
    , "Document number"
    , "Document type"
    , "Issue date"
    , "Document value"
    , "Remark value"
    , "Net value"
    , "Month"
    , "Year"
    , "Installment"
    , "Passenger"
    , "Leg of the trip"
    , "Batch number"
    , "Reimbursement number"
    , "Reimbursement value"
    , "Applicant ID"
    ]


isSearchable : ( String, String ) -> Bool
isSearchable ( field, label ) =
    List.member field
        [ "applicant_id"
        , "cnpj_cpf"
        , "congressperson_id"
        , "document_id"
        , "document_type"
        , "month"
        , "party"
        , "reimbursement_number"
        , "state"
        , "subquota_group_id"
        , "subquota_number"
        , "term"
        , "year"
        ]


sets : List ( Int, ( String, List String ) )
sets =
    List.indexedMap
        (,)
        [ ( "Reimbursement data"
          , [ "document_id"
            , "document_type"
            , "applicant_id"
            , "reimbursement_number"
            , "subquota_number"
            , "subquota_group_id"
            ]
          )
        , ( "Congressperson data"
          , [ "congressperson_id"
            , "party"
            , "state"
            , "term"
            ]
          )
        , ( "Expense data"
          , [ "cnpj_cpf"
            , "year"
            , "month"
            ]
          )
        ]
