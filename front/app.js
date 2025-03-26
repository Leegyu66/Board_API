const API_URL = "http://localhost:8080";  // 백엔드 API 주소 (필요에 따라 수정)

// DOM 요소 (로그인/로그아웃/게시판 등)
const loginForm = document.getElementById("loginForm");
const logoutButton = document.getElementById("logoutButton");
const boardSection = document.getElementById("boardSection");
const boardList = document.getElementById("boardList");
const createPostButton = document.getElementById("createPostButton");
const createPostForm = document.getElementById("createPostForm");
const submitPostButton = document.getElementById("submitPostButton");
const cancelPostButton = document.getElementById("cancelPostButton");
const postTitleInput = document.getElementById("postTitle");
const postContentInput = document.getElementById("postContent");
const editPostButton = document.getElementById("editPostButton");
const detailTitle = document.getElementById("detailTitle");
const detailContent = document.getElementById("detailContent");
const postDetails = document.getElementById("postDetails");
const detailViewcnt = document.getElementById("detailViewcnt");
const closePostDetailsButton = document.getElementById("closePostDetails");

// (NEW) 회원가입 관련
const showSignupFormButton = document.getElementById("showSignupForm");
const signupForm = document.getElementById("signupForm");
const cancelSignupButton = document.getElementById("cancelSignupButton");
// ★ 여기서 name/email/loginId/password 인풋을 실제로 가져오도록 해야 함
//   (HTML 폼에서 id="name", "email", "loginId", "password" 로 작성)

// 현재 수정 중인 글 ID
let currentPostId = null;

/* ----------------------------
   (A) 회원가입 로직
---------------------------- */
// 1) "Sign Up" 버튼 → 폼 열기
showSignupFormButton.addEventListener("click", () => {
  signupForm.style.display = "block";
});

// 2) "Cancel" 버튼 → 폼 숨기기 & 필드 초기화
cancelSignupButton.addEventListener("click", () => {
  signupForm.style.display = "none";
  document.getElementById("name").value = "";
  document.getElementById("email").value = "";
  document.getElementById("loginId").value = "";
  document.getElementById("password").value = "";
});

// 3) 회원가입 폼 submit → JSON으로 서버 전송
signupForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  // 폼에서 값 가져오기
  const nameValue = document.getElementById("name").value;
  const emailValue = document.getElementById("email").value;
  const loginIdValue = document.getElementById("loginId").value;
  const passwordValue = document.getElementById("password").value;

  // 필수 값 체크
  if (!nameValue || !emailValue || !loginIdValue || !passwordValue) {
    alert("All fields (name, email, login_id, password) are required.");
    return;
  }

  // 서버에 보낼 데이터 (JSON)
  const payload = {
    name: nameValue,
    email: emailValue,
    login_id: loginIdValue,  // key가 login_id
    password: passwordValue
  };

  try {
    // axios.post 로 JSON 형식 전송
    await axios.post(`${API_URL}/user`, payload);
    
    alert("Sign Up Success!");
    
    // 폼 초기화 & 숨기기
    signupForm.style.display = "none";
    document.getElementById("name").value = "";
    document.getElementById("email").value = "";
    document.getElementById("loginId").value = "";
    document.getElementById("password").value = "";
  } catch (error) {
    alert("Sign Up failed!");
    console.error(error);
  }
});

/* ----------------------------
   (B) 로그인 로직
---------------------------- */
loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const username = document.getElementById("username").value;
  const password = document.getElementById("password").value;
  
  try {
    // 로그인은 x-www-form-urlencoded 예시
    const loginData = new URLSearchParams();
    loginData.append("username", username);
    loginData.append("password", password);

    const response = await axios.post(
      `${API_URL}/user/login`,
      loginData,
      { headers: { "Content-Type": "application/x-www-form-urlencoded" } }
    );

    // 토큰을 쿠키에 저장
    document.cookie = `access_token=${response.data.access_token}; path=/`;
    
    // 로그인 성공 시 UI 변경
    loginForm.style.display = "none";
    signupForm.style.display = "none";
    showSignupFormButton.style.display = "none";
    
    boardSection.style.display = "block";
    logoutButton.style.display = "inline-block";
    
    loadBoardPosts();
  } catch (error) {
    alert("Login failed!");
    console.error(error);
  }
});

/* ----------------------------
   (C) 로그아웃
---------------------------- */
logoutButton.addEventListener("click", async () => {
  try {
    await axios.post(
      `${API_URL}/user/logout`,
      {},
      { headers: { "Authorization": `Bearer ${getCookie("access_token")}` } }
    );

    // 토큰 제거
    document.cookie = "access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";

    // UI 전환
    boardSection.style.display = "none";
    logoutButton.style.display = "none";

    loginForm.style.display = "block";
    showSignupFormButton.style.display = "inline-block";
  } catch (error) {
    alert("Logout failed!");
    console.error(error);
  }
});

/* ----------------------------
   (D) 게시판 로직
---------------------------- */
async function loadBoardPosts() {
  try {
    const response = await axios.get(`${API_URL}/board`, {
      headers: { "Authorization": `Bearer ${getCookie("access_token")}` }
    });

    boardList.innerHTML = "";
    response.data.forEach(post => {
      const listItem = document.createElement("li");
      listItem.textContent = post.title;

      // 상세 보기
      listItem.addEventListener("click", async () => {
        try {
          const res = await axios.get(`${API_URL}/board/${post.id}`, {
            headers: { "Authorization": `Bearer ${getCookie("access_token")}` }
          });
          const board = res.data;
          currentPostId = post.id;

          detailTitle.textContent = board.title;
          detailContent.textContent = board.content;
          detailViewcnt.textContent = `View Count: ${board.view_cnt}`;
          postDetails.style.display = "block";
        } catch (error) {
          alert("글을 불러오는 데 실패!");
          console.error(error);
        }
      });

      // 삭제 버튼
      const deleteButton = document.createElement("button");
      deleteButton.textContent = "삭제";
      deleteButton.style.marginLeft = "10px";
      deleteButton.addEventListener("click", async (e) => {
        e.stopPropagation(); // li 클릭 이벤트 중단
        if (confirm("정말 삭제하시겠습니까?")) {
          try {
            await axios.delete(`${API_URL}/board/${post.id}`, {
              headers: { "Authorization": `Bearer ${getCookie("access_token")}` }
            });
            alert("삭제 완료!");
            postDetails.style.display = "none";
            loadBoardPosts();
          } catch (error) {
            alert("삭제 실패!");
            console.error(error);
          }
        }
      });

      listItem.appendChild(deleteButton);
      boardList.appendChild(listItem);
    });
  } catch (error) {
    alert("Failed to load board posts");
    console.error(error);
  }
}

// 상세 보기 닫기
closePostDetailsButton.addEventListener("click", () => {
  postDetails.style.display = "none";
});

// 글 작성 폼 열기
createPostButton.addEventListener("click", () => {
  createPostForm.style.display = "block";
  submitPostButton.textContent = "Submit";
  currentPostId = null;
});

// 글 작성 / 수정
submitPostButton.addEventListener("click", async () => {
  const title = postTitleInput.value;
  const content = postContentInput.value;

  if (!title || !content) {
    alert("Both title and content are required.");
    return;
  }

  try {
    if (currentPostId) {
      // 글 수정
      await axios.patch(
        `${API_URL}/board/${currentPostId}`,
        { title, content },
        { headers: { "Authorization": `Bearer ${getCookie("access_token")}` } }
      );
      alert("수정 완료!");
    } else {
      // 새 글 작성
      await axios.post(
        `${API_URL}/board`,
        { title, content },
        { headers: { "Authorization": `Bearer ${getCookie("access_token")}` } }
      );
      alert("작성 완료!");
    }

    // 폼 초기화 & 게시판 재로드
    postTitleInput.value = "";
    postContentInput.value = "";
    createPostForm.style.display = "none";
    submitPostButton.textContent = "Submit";
    currentPostId = null;

    loadBoardPosts();
  } catch (error) {
    alert("등록 실패!");
    console.error(error);
  }
});

// 글 작성 취소
cancelPostButton.addEventListener("click", () => {
  createPostForm.style.display = "none";
  submitPostButton.textContent = "Submit";
  currentPostId = null;
});

// 글 수정 버튼 (상세 보기 영역)
editPostButton.addEventListener("click", () => {
  if (!currentPostId) return;
  postTitleInput.value = detailTitle.textContent;
  postContentInput.value = detailContent.textContent;
  createPostForm.style.display = "block";
  submitPostButton.textContent = "Update";
  postDetails.style.display = "none";
});

/* ----------------------------
   (E) 쿠키 가져오기 헬퍼
---------------------------- */
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(";").shift();
  return null;
}