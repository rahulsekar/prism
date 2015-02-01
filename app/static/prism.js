var app = angular.module("prism", ["ngRoute"])
    .config(function($routeProvider, $locationProvider) {
	$routeProvider
	    .when("/yield_curve", {
		templateUrl: "/static/yield_curve.html",
		controller: "YCController"
	    })
	    .when("/data_status", {
		templateUrl: "/static/data_status.html",
		controller: "DataStatusController"
	    })
    })

app.controller("MainController", function($scope, $route, $routeParams, $location, $window){
    $scope.isactive = function(page){
	return $location.path().indexOf(page) == 0
    }
})

app.controller("DataStatusController", function($scope, $http, $route){
    $scope.load = function(date){
	var prepare = "/prepare/data_load/" + date
	$http.get(prepare).success(function(response){
	    $route.reload()
	})
    }

    var json = "/static/json/data_status.json"
    var prepare = "/prepare/data_status"
    $http.get(prepare).success(function(response){
	$http.get(json).success(function(response){
	    $scope.data=response
	})
    })
})

app.controller("YCController", function($scope, $route, $routeParams, $location, $http){
    $scope.set_asof = function(date){
	if( $scope.asof != date ){
	    $scope.date = $scope.asof = date
	    var json = "/static/json/yc_" + $scope.asof + ".json"
	    var prepare = "/prepare/yield_curve/" + $scope.asof
	    $http.get(prepare).success(function(response){
		$http.get(json).success(function(response){
		    $scope.data=response
		})
	    })
	}
    }
    $scope.set_asof("2015-01-09")
})
