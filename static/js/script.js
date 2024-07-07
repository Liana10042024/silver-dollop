$(document).ready(function() {
    // 툴팁 초기화
    $('[data-toggle="tooltip"]').tooltip({
        html: true,
        placement: 'top'
    });

    // 검색 버튼 클릭 이벤트
    $('#searchButton').click(function() {
        var situation = $('#situation').val();
        
        // API 서버 URL (실제 서버 주소로 변경 필요)
        var apiUrl = 'https://api.odcloud.kr/api/15069932/v1/uddi:3799441a-4012-4caa-9955-b4d20697b555';

        $.ajax({
            url: apiUrl,
            method: 'POST',
            data: JSON.stringify({ situation: situation }),
            contentType: 'application/json',
            success: function(response) {
                // 결과 페이지로 이동하면서 데이터 전달
                localStorage.setItem('searchResult', JSON.stringify(response));
                window.location.href = 'result.html';
            },
            error: function(xhr, status, error) {
                alert('검색 중 오류가 발생했습니다. 다시 시도해주세요.');
            }
        });
    });

    // 결과 페이지 로드 시 결과 표시
    if (window.location.pathname.endsWith('result.html')) {
        var result = JSON.parse(localStorage.getItem('searchResult'));
        if (result) {
            $('#resultBox').html(result.processed_summary);
            
            // 법률 용어에 툴팁 적용
            $('.legal-term').tooltip({
                html: true,
                placement: 'top'
            });
        }
    }
});