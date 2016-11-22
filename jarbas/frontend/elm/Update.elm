module Update exposing (Flags, Msg(..), update, updateFromFlags)

import Documents.Update
import Documents.Decoder
import Internationalization exposing (Language(..), TranslationId(..), translate)
import Material
import String
import Model exposing (Model, model)


type alias Flags =
    { lang : String
    , googleStreetViewApiKey : String
    }


type Msg
    = DocumentsMsg Documents.Update.Msg
    | LayoutMsg Msg
    | Mdl (Material.Msg Msg)


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        DocumentsMsg msg ->
            let
                updated =
                    Documents.Update.update msg model.documents

                documents =
                    fst updated

                cmd =
                    Cmd.map DocumentsMsg <| snd updated
            in
                ( { model | documents = documents }, cmd )

        LayoutMsg _ ->
            ( model, Cmd.none )

        Mdl mdlMsg ->
            Material.update mdlMsg model


updateFromFlags : Flags -> Model -> Model
updateFromFlags flags model =
    let
        lang =
            if String.toLower flags.lang == "pt" then
                Portuguese
            else
                English

        googleStreetViewApiKey =
            flags.googleStreetViewApiKey

        newDocuments =
            Documents.Decoder.updateLanguage lang model.documents
                |> Documents.Decoder.updateGoogleStreetViewApiKey googleStreetViewApiKey

        layout =
            model.layout

        newLayout =
            { layout | lang = lang }
    in
        { model
            | documents = newDocuments
            , layout = newLayout
            , googleStreetViewApiKey = googleStreetViewApiKey
            , lang = lang
        }
