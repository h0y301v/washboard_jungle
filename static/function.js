$(document).ready(function () {
    if ($.cookie('mytoken')) {
        showDay();
        booked();
    }
});
// jwt 디코드용 함수
function parseJwt(token) {
    var base64Url = token.split('.')[1];
    var base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    var jsonPayload = decodeURIComponent(window.atob(base64).split('').map(function (c) {
        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
    }).join(''));

    return JSON.parse(jsonPayload);
}

// 로그인
function login() {
    $.ajax({
        type: "POST",
        url: "/api/login",
        data: { id_login: $('#userid').val(), pw_login: $('#userpw').val() },

        success: function (response) {
            if (response['result'] == 'fail') {
                alert(response['msg'])
            } else {
                alert('로그인 완료!')
                window.location.href = '/'
            }
        }
    })
}

function showDay() {
    $.ajax({
        type: "GET",
        url: "/showday",
        data: {},
        success: function (response) {
            let id = response["cards"];

            for (let i = 0; i < id.length; i++) {
                makeCard(i, id[i]["id"])

            }
        }
    })
}
// 달력(카드 생성)
function makeCard(num, id) {
    if (id == "none") {
        color = "FFFFFF"
    }
    else {
        // id를 컬러 6자리로 변환, 글자 색은 대비되게 흰/검 중에 나오게 만듦
        function hash(string) {
            digits = 9
            var m = Math.pow(10, digits + 1) - 1;
            var phi = Math.pow(10, digits) / 2 - 1;
            var n = 0;
            for (var i = 0; i < string.length; i++) {
                n = (n + phi * string.charCodeAt(i)) % m;
            }
            return n % 16777215;
        }
        color = hash(id).toString(16)
        while (color.length < 6) {
            color += "0"
        }
        console.log(color)
    }
    function getContrast(hexcolor) {
        hexcolor = hexcolor.replace("#", "");
        var r = parseInt(hexcolor.substr(0, 2), 16);
        var g = parseInt(hexcolor.substr(2, 2), 16);
        var b = parseInt(hexcolor.substr(4, 2), 16);
        var yiq = ((r * 299) + (g * 587) + (b * 114)) / 1000;
        return (yiq >= 100) ? 'black' : 'white';
    }

    fontcolor = getContrast(color)
    let temp_html
    if (id == "none") {
        temp_html = `<div class="cards" style="background-color: #${color}; color:${fontcolor};" onClick="book('${num}','${id}')" > 빈 시간입니다 </div>`;
    }
    else {
        temp_html = `<div class="cards" style="background-color: #${color}; color:${fontcolor};" onClick="book(${num}, ${parseInt(id)})" > 예약자 : ${id}</div>`;
    }
    $("#cards-box").append(temp_html);

}
// 예약기능
function book(num, id) {

    $.ajax({
        type: "POST",
        url: "/api/book",
        data: { card_num: num, card_id: id },
        success: function (response) {
            if (response['result'] == 'success') {
                window.location.href = '/washboard'
            } else if (response['refresh'] == 1) {
                alert(response['msg'])
                window.location.reload()
            }
            else if (response['result'] == 'fail') {
                alert(response['msg'])
            }
        }
    })
}
// 예약확인, 하단보다는 상단이 좋은 것 같아서 상단에 표시하기로 변경함
function booked() {
    id = parseJwt($.cookie('mytoken'))['id']
    let temp_html
    let min, max, day
    $.ajax({
        type: "POST",
        url: "/booked",
        data: { user_id: id },
        success: function (response) {
            min = parseInt(response['min'])
            max = parseInt(response['max'])
            if (min >= 240) {
                day = "326호"
            }
            else {
                day = "325호"
            }
            // now = [월일,시작시간,끝나는시간,요일]
            temp_html = `${id}님 ${response['now'][2]} ${response['now'][0]}~${response['now'][1]}, ${day} 예약`;
            $("#booked").append(temp_html);
        }
    })

}