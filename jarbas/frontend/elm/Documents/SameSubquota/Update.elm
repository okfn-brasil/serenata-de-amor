module Documents.SameSubquota.Update exposing (Filter, load)

import Documents.RelatedTable.Update exposing (Msg, loadUrl)
import Format.Url exposing (url)


type alias Filter =
    { applicantId : Int
    , year : Int
    , month : Int
    , subquotaId : Int
    }


{-| Creates an URL from a Filter:

    >>> getUrl { year = 2016, applicantId = 13,  subquotaId = 42, month = 2 }
    "/api/reimbursement/2016/13/?format=json&month=2&subquotaId=42

-}
getUrl : Filter -> String
getUrl filter =
    let
        base : String
        base =
            String.concat
                [ "/api/reimbursement/"
                , toString filter.year
                , "/"
                , toString filter.applicantId
                , "/"
                ]
    in
        url base
            [ ( "format", "json" )
            , ( "month", toString filter.month )
            , ( "subquota_id", toString filter.subquotaId )
            ]


load : Filter -> Cmd Msg
load filter =
    filter
        |> getUrl
        |> loadUrl
