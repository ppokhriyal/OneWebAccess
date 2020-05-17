// //Table Pagination
// $(document).ready(function(){
// 	$('#tablepaginate').DataTable({
// 		"pagingType": "simple",
// 		"ordering": false
// 	});
// 	$('.dataTables_length').addClass('bs-select');
// });


$(document).ready(function() {
    $('#tablepaginate').DataTable( {
        "pagingType": "full_numbers"
    } );
} );