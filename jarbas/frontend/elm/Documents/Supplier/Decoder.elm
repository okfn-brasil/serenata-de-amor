module Documents.Supplier.Decoder exposing (decoder)

import Json.Decode exposing ((:=))
import Json.Decode.Pipeline exposing (decode, nullable, required)
import Documents.Supplier.Model exposing (Supplier, Activity)


decoder : Json.Decode.Decoder Supplier
decoder =
    decode Supplier
        |> required "main_activity" decodeActivities
        |> required "secondary_activity" decodeActivities
        |> required "cnpj" Json.Decode.string
        |> required "opening" (nullable Json.Decode.string)
        |> required "legal_entity" (nullable Json.Decode.string)
        |> required "trade_name" (nullable Json.Decode.string)
        |> required "name" (nullable Json.Decode.string)
        |> required "type" (nullable Json.Decode.string)
        |> required "status" (nullable Json.Decode.string)
        |> required "situation" (nullable Json.Decode.string)
        |> required "situation_reason" (nullable Json.Decode.string)
        |> required "situation_date" (nullable Json.Decode.string)
        |> required "special_situation" (nullable Json.Decode.string)
        |> required "special_situation_date" (nullable Json.Decode.string)
        |> required "responsible_federative_entity" (nullable Json.Decode.string)
        |> required "address" (nullable Json.Decode.string)
        |> required "number" (nullable Json.Decode.string)
        |> required "additional_address_details" (nullable Json.Decode.string)
        |> required "neighborhood" (nullable Json.Decode.string)
        |> required "zip_code" (nullable Json.Decode.string)
        |> required "city" (nullable Json.Decode.string)
        |> required "state" (nullable Json.Decode.string)
        |> required "email" (nullable Json.Decode.string)
        |> required "phone" (nullable Json.Decode.string)
        |> required "latitude" (nullable Json.Decode.string)
        |> required "longitude" (nullable Json.Decode.string)
        |> required "last_updated" (nullable Json.Decode.string)


decodeActivities : Json.Decode.Decoder (List Activity)
decodeActivities =
    Json.Decode.list <|
        Json.Decode.object2 Activity
            (Json.Decode.at [ "code" ] Json.Decode.string)
            (Json.Decode.at [ "description" ] Json.Decode.string)
