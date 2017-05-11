module Reimbursement.SameDay.Update exposing (..)

import Reimbursement.RelatedTable.Update exposing (Msg, loadUrl)
import String


{-| Creates an URL from an UniqueId:

    >>> getUrl 42
    "/api/reimbursement/42/same_day/?format=json"

-}
getUrl : Int -> String
getUrl documentId =
    String.join
        "/"
        [ "/api"
        , "reimbursement"
        , toString documentId
        , "same_day/?format=json"
        ]
        |> Debug.log "url"


load : Int -> Cmd Msg
load documentId =
    documentId
        |> getUrl
        |> loadUrl
