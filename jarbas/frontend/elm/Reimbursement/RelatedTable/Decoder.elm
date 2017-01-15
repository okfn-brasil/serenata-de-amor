module Reimbursement.RelatedTable.Decoder exposing (decoder)

import Json.Decode exposing (array, float, int, nullable, string)
import Json.Decode.Pipeline exposing (decode, hardcoded, optional, required)
import Reimbursement.RelatedTable.Model exposing (ReimbursementSummary, Results)


reimbursementSummaryDecoder : Json.Decode.Decoder ReimbursementSummary
reimbursementSummaryDecoder =
    decode ReimbursementSummary
        |> required "applicant_id" int
        |> optional "city" (nullable string) Nothing
        |> required "document_id" int
        |> required "subquota_description" string
        |> required "subquota_id" int
        |> required "supplier" string
        |> required "total_net_value" float
        |> required "year" int
        |> hardcoded False


decoder : Json.Decode.Decoder Results
decoder =
    decode Results
        |> required "results" (array reimbursementSummaryDecoder)
        |> required "next" (nullable string)
