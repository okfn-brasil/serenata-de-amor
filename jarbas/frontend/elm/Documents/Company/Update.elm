module Documents.Company.Update exposing (Msg(..), load, update)

import Char
import Documents.Company.Decoder exposing (decoder)
import Documents.Company.Model exposing (Model, Company)
import Format.Url exposing (url)
import Http
import Material
import String


type Msg
    = SearchCompany String
    | LoadCompany (Result Http.Error Company)
    | Mdl (Material.Msg Msg)


cleanUp : String -> String
cleanUp cnpj =
    String.filter Char.isDigit cnpj


isValid : String -> Bool
isValid cnpj =
    if String.length (cleanUp cnpj) == 14 then
        True
    else
        False


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        SearchCompany cnpj ->
            if isValid cnpj then
                ( { model | loading = True }, load cnpj )
            else
                ( { model | loaded = True, company = Nothing }, Cmd.none )

        LoadCompany (Ok company) ->
            ( { model | company = Just company, loading = False, loaded = True }, Cmd.none )

        LoadCompany (Err error) ->
            let
                err =
                    Debug.log "ApiError" (toString error)
            in
                ( { model | loaded = True, error = Just error }, Cmd.none )

        Mdl mdlMsg ->
            Material.update mdlMsg model


load : String -> Cmd Msg
load cnpj =
    if isValid cnpj then
        let
            path =
                "/api/company/" ++ (cleanUp cnpj) ++ "/"

            query =
                [ ( "format", "json" ) ]
        in
            decoder
                |> Http.get (url path query)
                |> Http.send LoadCompany
    else
        Cmd.none
