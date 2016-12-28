module Documents.Company.Decoder exposing (decoder)

import Json.Decode exposing (nullable, string)
import Json.Decode.Pipeline exposing (decode, required)
import Documents.Company.Model exposing (Company, Activity)


decoder : Json.Decode.Decoder Company
decoder =
    decode Company
        |> required "main_activity" decodeActivities
        |> required "secondary_activity" decodeActivities
        |> required "cnpj" string
        |> required "opening" (nullable string)
        |> required "legal_entity" (nullable string)
        |> required "trade_name" (nullable string)
        |> required "name" (nullable string)
        |> required "type" (nullable string)
        |> required "status" (nullable string)
        |> required "situation" (nullable string)
        |> required "situation_reason" (nullable string)
        |> required "situation_date" (nullable string)
        |> required "special_situation" (nullable string)
        |> required "special_situation_date" (nullable string)
        |> required "responsible_federative_entity" (nullable string)
        |> required "address" (nullable string)
        |> required "number" (nullable string)
        |> required "additional_address_details" (nullable string)
        |> required "neighborhood" (nullable string)
        |> required "zip_code" (nullable string)
        |> required "city" (nullable string)
        |> required "state" (nullable string)
        |> required "email" (nullable string)
        |> required "phone" (nullable string)
        |> required "latitude" (nullable string)
        |> required "longitude" (nullable string)
        |> required "last_updated" (nullable string)


decodeActivities : Json.Decode.Decoder (List Activity)
decodeActivities =
    Json.Decode.list <|
        Json.Decode.map2 Activity
            (Json.Decode.at [ "code" ] string)
            (Json.Decode.at [ "description" ] string)
