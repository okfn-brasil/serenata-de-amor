module Documents.Receipt.Decoder exposing (decoder, urlDecoder)

import Json.Decode exposing (at, bool, nullable, string)
import Json.Decode.Pipeline exposing (decode, hardcoded, required)
import Internationalization exposing (Language(..), TranslationId(..), translate)
import Material
import Documents.Receipt.Model exposing (Model, ReimbursementId)


urlDecoder : Json.Decode.Decoder (Maybe String)
urlDecoder =
    at [ "url" ] (nullable string)


decoder : Language -> Json.Decode.Decoder Model
decoder lang =
    decode Model
        |> hardcoded Nothing
        |> required "url" (nullable string)
        |> required "fetched" bool
        |> hardcoded False
        |> hardcoded Nothing
        |> hardcoded lang
        |> hardcoded Material.model
