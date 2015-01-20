var app = angular.module("prism", []);

app.controller("prismCtrl", function($scope, $http){

    $scope.set_asof = function(asof){
	$scope.ycdate = asof
	$http.get(window.location.origin + "/bonds/" + asof).success(function(response){$scope.bnds=response;})
    }

    $scope.asof = "2015-01-09"
    $scope.set_asof($scope.asof)
});
