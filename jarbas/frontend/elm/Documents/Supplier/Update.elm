module Documents.Supplier.Update exposing (Msg(..), load, update)

import Char
import Http exposing (url)
import Material
import String
import Task
import Documents.Supplier.Model exposing (Model, Supplier)
import Documents.Supplier.Decoder exposing (decoder)


type Msg
    = LoadSupplier String
    | ApiSuccess Supplier
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
        LoadSupplier cnpj ->
            if isValid cnpj then
                ( { model | loading = True }, load cnpj )
            else
                ( { model | loaded = True, supplier = Nothing }, Cmd.none )

        ApiSuccess supplier ->
            ( { model | supplier = Just supplier, loading = False, loaded = True }, Cmd.none )

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
    let
        query =
            [ ( "format", "json" ) ]

        path =
            "/api/supplier/" ++ (cleanUp cnpj)

        url =
            Http.url path query
    in
        if path == "/api/supplier/" then
            Cmd.none
        else
            Task.perform
                ApiFail
                ApiSuccess
                (Http.get decoder url)
