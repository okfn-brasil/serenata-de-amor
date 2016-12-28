module Documents.SameDay.Decoder exposing (decoder)

import Documents.SameDay.Model exposing (Results, DocumentSummary)
import Json.Decode exposing (float, int, list, nullable, string)
import Json.Decode.Pipeline exposing (decode, hardcoded, required)


documentSummaryDecoder : Json.Decode.Decoder (List DocumentSummary)
documentSummaryDecoder =
    decode DocumentSummary
        |> required "applicant_id" int
        |> required "city" (nullable string)
        |> required "document_id" int
        |> required "subquota_description" string
        |> required "subquota_id" int
        |> required "supplier" string
        |> required "total_net_value" float
        |> required "year" int
        |> hardcoded False
        |> list


decoder : Json.Decode.Decoder Results
decoder =
    decode Results
        |> required "results" documentSummaryDecoder
        |> required "next" (nullable string)
