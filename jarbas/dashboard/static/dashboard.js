/*
 *
 * This JS assures backward compatibility for URLs aiming at the Layers app
 * version os a receipt, i.e. the Elm interface.
 *
 * Old URLs such as:
 * https://domain.tld/#/documentId/42
 *
 * will be redirected by the backend to:
 * https://domain.tld//dashboard/chamber_of_deputies/reimbursement/#/documentId/42
 *
 * and then this JS will correct it to:
 * https://domain.tld/layers/#/documentId/42
 *
 * */

var redirectedPath = '/dashboard/chamber_of_deputies/reimbursement/';
var layersPath = '/layers/';
var hash = 'documentId'; // we look only for fragments containing this word

var isLayersUrl = function () {
  if (redirectedPath !== window.location.pathname) return false;
  return window.location.hash.split('/').includes(hash);
};

var redirectToLayers = function () {
  if (isLayersUrl()) window.location.pathname =layersPath;
};

redirectToLayers();
