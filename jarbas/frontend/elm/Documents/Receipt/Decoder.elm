module Documents.Receipt.Decoder exposing (decoder, urlDecoder)

import Json.Decode
import Json.Decode.Pipeline exposing (decode, hardcoded, nullable, required)
import Internationalization exposing (Language(..), TranslationId(..), translate)
import Material
import Json.Decode exposing (at, maybe, string)
import Documents.Receipt.Model exposing (Model)


urlDecoder : Json.Decode.Decoder (Maybe String)
urlDecoder =
    at [ "url" ] (maybe string)


decoder : Language -> Json.Decode.Decoder Model
decoder lang =
    decode Model
        |> required "url" (nullable Json.Decode.string)
        |> required "fetched" Json.Decode.bool
        |> hardcoded False
        |> hardcoded Nothing
        |> hardcoded lang
        |> hardcoded Material.model
