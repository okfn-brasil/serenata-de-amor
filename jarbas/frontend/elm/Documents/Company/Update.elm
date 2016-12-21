module Documents.Company.Update exposing (Msg(..), load, update)

import Char
import Http exposing (url)
import Material
import String
import Task
import Documents.Company.Model exposing (Model, Company)
import Documents.Company.Decoder exposing (decoder)


type Msg
    = LoadCompany String
    | ApiSuccess Company
    | ApiFail Http.Error
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
        LoadCompany cnpj ->
            if isValid cnpj then
                ( { model | loading = True }, load cnpj )
            else
                ( { model | loaded = True, company = Nothing }, Cmd.none )

        ApiSuccess company ->
            ( { model | company = Just company, loading = False, loaded = True }, Cmd.none )

        ApiFail error ->
            let
                err =
                    Debug.log (toString error)
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

            url =
                Http.url path [ ( "format", "json" ) ]
        in
            Task.perform
                ApiFail
                ApiSuccess
                (Http.get decoder url)
    else
        Cmd.none
