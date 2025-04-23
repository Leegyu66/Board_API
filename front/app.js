// -----------------------------
//  app.js (SR 기능 최종 통합 버전)
// -----------------------------

// ★ CORS 환경에서 쿠키 전송을 허용하려면
axios.defaults.withCredentials = true;   // 모든 요청에 쿠키/인증정보 포함

// const API_URL = "http://3.39.195.46:8080";  // 백엔드 API 주소 (필요에 따라 수정)
const API_URL = "http://192.168.100.145:8080"

// --- 기존 DOM 요소들 ---
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
const showSignupFormButton = document.getElementById("showSignupForm");
const signupForm = document.getElementById("signupForm");
const cancelSignupButton = document.getElementById("cancelSignupButton");
const loggedUserSpan = document.getElementById("loggedUser");

// --- SR 관련 DOM 요소들 ---
const srSection = document.getElementById("srSection"); // SR 섹션 전체
const srImageInput = document.getElementById("srImageInput");
const srUploadButton = document.getElementById("srUploadButton");
const srStatus = document.getElementById("srStatus");
const srResultImage = document.getElementById("srResultImage");

// --- 전역 변수 ---
let currentPostId = null; // 현재 수정/상세보기 중인 게시글 ID
let srSelectedFile = null; // SR용으로 선택된 파일 객체
let srBase64ImageString = null; // SR용 Base64 인코딩된 이미지 문자열

/* ================================================
   (E) 쿠키 가져오기 헬퍼
================================================ */
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) {
    return parts.pop().split(";").shift();
  }
  return null;
}

/* ================================================
   사용자 정보 불러오기
================================================ */
async function loadUserName() {
  const token = getCookie("access_token");
  if (!token) {
    console.log("loadUserName: No token found.");
    loggedUserSpan.textContent = ""; // 토큰 없으면 이름 지우기
    return; // 토큰 없으면 실행 안 함
  }

  try {
    const response = await axios.get(`${API_URL}/user`, {
      headers: { "Authorization": `Bearer ${token}` },
      timeout: 5000 // 5초 타임아웃 설정
    });
    const userName = response.data.name;
    loggedUserSpan.textContent = userName ? `(${userName})` : "";
    console.log("User info loaded:", userName);
  } catch (error) {
    console.error("Failed to load user info:", error);
    loggedUserSpan.textContent = ""; // 에러 시 이름 지우기
    // 토큰 만료 등의 경우 로그아웃 처리
    if (error.response && (error.response.status === 401 || error.response.status === 403)) {
        console.log("Token invalid/expired, logging out.");
        handleLogout(); // 로그아웃 함수 호출
    } else {
        // 네트워크 오류 등 다른 문제일 수 있음
        alert("사용자 정보를 불러오는 데 실패했습니다. 잠시 후 다시 시도해주세요.");
    }
    // 에러를 다시 던져서 호출한 쪽(DOMContentLoaded)에서 인지하도록 함
    throw error;
  }
}


/* ================================================
   (A) 회원가입 로직
================================================ */
if (showSignupFormButton && signupForm && cancelSignupButton) {
  showSignupFormButton.addEventListener("click", () => {
    signupForm.style.display = "block";
    loginForm.style.display = "none"; // 로그인 폼 숨기기
  });

  cancelSignupButton.addEventListener("click", () => {
    signupForm.style.display = "none";
    loginForm.style.display = "block"; // 로그인 폼 다시 보이기
    // 입력 필드 초기화
    try {
      document.getElementById("name").value = "";
      document.getElementById("email").value = "";
      document.getElementById("loginId").value = "";
      document.getElementById("signupPassword").value = "";
    } catch(e) { console.warn("Signup form elements not found for reset."); }
  });

  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const nameValue = document.getElementById("name")?.value;
    const emailValue = document.getElementById("email")?.value;
    const loginIdValue = document.getElementById("loginId")?.value;
    const passwordValue = document.getElementById("signupPassword")?.value;

    if (!nameValue || !emailValue || !loginIdValue || !passwordValue) {
      alert("모든 필드를 입력해주세요.");
      return;
    }
    const payload = { name: nameValue, email: emailValue, login_id: loginIdValue, password: passwordValue };

    try {
      await axios.post(`${API_URL}/user`, payload);
      alert("회원가입 성공! 이제 로그인해주세요.");
      signupForm.style.display = "none";
      loginForm.style.display = "block"; // 로그인 폼 보이기
       // 입력 필드 초기화
       try {
        document.getElementById("name").value = "";
        document.getElementById("email").value = "";
        document.getElementById("loginId").value = "";
        document.getElementById("signupPassword").value = "";
       } catch(e) {}
    } catch (error) {
      alert("회원가입 실패! " + (error.response?.data?.detail || error.message));
      console.error(error);
    }
  });
} else {
    console.warn("Signup related elements not found.");
}

/* ================================================
   (B) 로그인 로직
================================================ */
if (loginForm && signupForm && showSignupFormButton && boardSection && logoutButton && srSection) {
  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const username = document.getElementById("username")?.value;
    const password = document.getElementById("password")?.value;
    if (!username || !password) {
        alert("아이디와 비밀번호를 입력해주세요.");
        return;
    }

    try {
      const loginData = new URLSearchParams();
      loginData.append("username", username);
      loginData.append("password", password);

      const response = await axios.post(`${API_URL}/user/login`, loginData, {
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
      });

      // SameSite=Lax 추가 (보안 강화), 필요시 Secure; HttpOnly; 추가
      document.cookie = `access_token=${response.data.access_token}; path=/; SameSite=Lax;`;
      console.log("Login successful, token set.");

      // UI 전환
      loginForm.style.display = "none";
      signupForm.style.display = "none";
      showSignupFormButton.style.display = "none";
      boardSection.style.display = "block";
      logoutButton.style.display = "inline-block";
      srSection.style.display = "block"; // *** SR 섹션 보이기 ***

      await loadUserName();
      loadBoardPosts();

    } catch (error) {
      alert("로그인 실패! 아이디 또는 비밀번호를 확인해주세요.");
      console.error("Login error:", error);
      loggedUserSpan.textContent = ""; // 에러 시 사용자 이름 초기화
    }
  });
} else {
    console.warn("Login related elements not found.");
}

/* ================================================
   (C) 로그아웃 로직 (함수)
================================================ */
async function handleLogout() {
  const token = getCookie("access_token");
  console.log("Attempting logout.");
  if (token) {
    try {
      // 서버에 로그아웃 요청 (선택 사항, 토큰 무효화 목적)
      await axios.post(
        `${API_URL}/user/logout`,
        {}, // 빈 바디
        { headers: { "Authorization": `Bearer ${token}` }, timeout: 3000 }
      );
       console.log("Logout API call successful.");
    } catch (error) {
      // 로그아웃 API 실패는 흔하며, 클라이언트 측 처리에 영향 안 줄 수 있음
      console.warn("Logout API call failed (might be okay if token expired/invalid):", error);
    }
  }
  // 클라이언트 측 쿠키 제거 (필수)
  document.cookie = "access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Lax";
  console.log("Access token cookie cleared.");

  // UI 초기화 (로그아웃 상태로)
  if (loginForm) loginForm.style.display = "block";
  if (signupForm) signupForm.style.display = "none";
  if (showSignupFormButton) showSignupFormButton.style.display = "inline-block";
  if (logoutButton) logoutButton.style.display = "none";
  if (boardSection) boardSection.style.display = "none";
  if (postDetails) postDetails.style.display = "none";
  if (createPostForm) createPostForm.style.display = "none";
  if (srSection) srSection.style.display = "none"; // *** SR 섹션 숨기기 ***
  if (loggedUserSpan) loggedUserSpan.textContent = "";
  currentPostId = null; // 현재 보고/수정 중인 글 ID 초기화
  console.log("UI reset to logged out state.");
}

if (logoutButton) {
    logoutButton.addEventListener("click", handleLogout);
} else {
     console.warn("Logout button not found.");
}


/* ================================================
   (D) 게시판 로직
================================================ */
async function loadBoardPosts() {
  const token = getCookie("access_token");
  if (!token) {
    console.warn("Cannot load board posts without token.");
    // 로그인 페이지로 리다이렉트 또는 메시지 표시 등의 처리 추가 가능
    return;
  }
  if (!boardList) {
    console.warn("Board list element not found.");
    return;
  }

  try {
    const response = await axios.get(`${API_URL}/board`, {
      headers: { "Authorization": `Bearer ${token}` },
    });

    boardList.innerHTML = ""; // 목록 초기화
    response.data.forEach(post => {
      const listItem = document.createElement("li");
      listItem.textContent = `${post.title} (작성자: ${post.name})`;
      listItem.setAttribute('data-post-id', post.id);

      // 상세보기 클릭 이벤트
      listItem.addEventListener("click", async (event) => {
         if (event.target.tagName === 'BUTTON') return; // 버튼 클릭 시 제외
         const postId = event.currentTarget.getAttribute('data-post-id');
         if (postDetails.style.display !== "none" && currentPostId === parseInt(postId)) {
           postDetails.style.display = "none";
           currentPostId = null;
         } else {
           await showPostDetails(postId);
         }
      });

      // 삭제 버튼 추가
      const deleteButton = document.createElement("button");
      deleteButton.textContent = "삭제";
      deleteButton.style.marginLeft = "10px";
      deleteButton.addEventListener("click", async (e) => {
        e.stopPropagation();
        const postId = e.target.closest('li').getAttribute('data-post-id');
        if (confirm("정말 삭제하시겠습니까?")) {
          await deletePost(postId);
        }
      });

      listItem.appendChild(deleteButton);
      boardList.appendChild(listItem);
    });
    console.log("Board posts loaded.");
  } catch (error) {
    alert("게시글 목록을 불러오는 데 실패했습니다.");
    console.error("Failed to load board posts:", error);
    if (error.response && (error.response.status === 401 || error.response.status === 403)) {
        handleLogout(); // 권한 없으면 로그아웃
    }
  }
}

// 게시글 상세 보기 함수
async function showPostDetails(postId) {
  const token = getCookie("access_token");
  if (!token) return;
  if (!postDetails || !detailTitle || !detailContent || !detailViewcnt) {
       console.warn("Detail view elements not found.");
       return;
  }

  try {
    const res = await axios.get(`${API_URL}/board/${postId}`, {
      headers: { "Authorization": `Bearer ${token}` },
    });
    const board = res.data;
    currentPostId = board.id;

    detailTitle.textContent = `${board.title} (작성자: ${board.name})`;
    detailContent.textContent = board.content;
    detailViewcnt.textContent = `View Count: ${board.view_cnt}`;
    postDetails.style.display = "block";
    if (createPostForm) createPostForm.style.display = "none";
  } catch (error) {
    alert("글 상세 정보를 불러오는 데 실패했습니다.");
    console.error("Failed to load post details:", error);
    currentPostId = null;
    postDetails.style.display = "none";
  }
}

// 게시글 삭제 함수
async function deletePost(postId) {
  const token = getCookie("access_token");
  if (!token) return;
  try {
    await axios.delete(`${API_URL}/board/${postId}`, {
      headers: { "Authorization": `Bearer ${token}` },
    });
    alert("삭제 완료!");
    if(postDetails) postDetails.style.display = "none";
    currentPostId = null;
    loadBoardPosts(); // 목록 새로고침
  } catch (error) {
    alert("삭제 실패!");
    console.error("Failed to delete post:", error);
  }
}

// 상세 보기 닫기 버튼 이벤트
if (closePostDetailsButton) {
  closePostDetailsButton.addEventListener("click", () => {
    if (postDetails) postDetails.style.display = "none";
    currentPostId = null;
  });
} else { console.warn("Close details button not found."); }

// 글 작성 폼 열기 버튼 이벤트
if (createPostButton && createPostForm && postTitleInput && postContentInput && submitPostButton && postDetails) {
  createPostButton.addEventListener("click", () => {
    postTitleInput.value = "";
    postContentInput.value = "";
    createPostForm.style.display = "block";
    submitPostButton.textContent = "Submit";
    currentPostId = null;
    postDetails.style.display = "none";
  });
} else { console.warn("Create post related elements not found."); }

// 글 작성/수정 폼 제출 이벤트
if (submitPostButton && postTitleInput && postContentInput && createPostForm) {
  submitPostButton.addEventListener("click", async () => {
    const title = postTitleInput.value;
    const content = postContentInput.value;
    const token = getCookie("access_token");

    if (!title || !content) {
      alert("제목과 내용을 모두 입력해주세요.");
      return;
    }
    if (!token) {
      alert("로그인이 필요합니다.");
      return;
    }

    const payload = { title, content };
    const url = currentPostId ? `${API_URL}/board/${currentPostId}` : `${API_URL}/board`;
    const method = currentPostId ? 'patch' : 'post';
    const action = currentPostId ? '수정' : '작성';

    try {
      await axios({ method, url, data: payload, headers: { "Authorization": `Bearer ${token}` } });
      alert(`${action} 완료!`);

      // 성공 후 폼 초기화 및 숨기기
      postTitleInput.value = "";
      postContentInput.value = "";
      createPostForm.style.display = "none";
      submitPostButton.textContent = "Submit"; // 버튼 텍스트 원복
      currentPostId = null;

      loadBoardPosts(); // 목록 새로고침
    } catch (error) {
      alert(`${action} 실패!`);
      console.error(`Failed to ${action} post:`, error);
    }
  });
} else { console.warn("Submit post related elements not found."); }

// 글 작성 취소 버튼 이벤트
if (cancelPostButton && createPostForm && postTitleInput && postContentInput && submitPostButton) {
  cancelPostButton.addEventListener("click", () => {
    createPostForm.style.display = "none";
    postTitleInput.value = "";
    postContentInput.value = "";
    submitPostButton.textContent = "Submit";
    currentPostId = null;
  });
} else { console.warn("Cancel post button or related elements not found."); }

// 글 수정 버튼 (상세 보기 영역 내) 이벤트
if (editPostButton && postDetails && createPostForm && postTitleInput && postContentInput && detailTitle && detailContent && submitPostButton) {
  editPostButton.addEventListener("click", () => {
    if (!currentPostId) return;
    const titleText = detailTitle.textContent.replace(/\s*\(작성자:.*\)\s*$/, "").trim();
    postTitleInput.value = titleText;
    postContentInput.value = detailContent.textContent;

    createPostForm.style.display = "block";
    submitPostButton.textContent = "Update";
    postDetails.style.display = "none";
    // currentPostId는 이미 설정됨
  });
} else { console.warn("Edit post related elements not found."); }


/* ============================================
   (F) Super Resolution 로직 추가
============================================ */

// SR 관련 DOM 요소들 (위에서 이미 선언됨)

// SR 이미지 파일 입력 변경 감지
if (srImageInput && srUploadButton && srStatus && srResultImage) {
  srImageInput.addEventListener('change', (event) => {
      srSelectedFile = event.target.files[0];
      srBase64ImageString = null;
      srResultImage.src = ""; // 결과 이미지 초기화

      if (srSelectedFile) {
          srStatus.textContent = `선택된 파일: ${srSelectedFile.name} (${srSelectedFile.type})`;
          srUploadButton.disabled = true; // 읽는 동안 비활성화

          const reader = new FileReader();

          reader.onload = function(loadEvent) {
              const dataUrl = loadEvent.target.result;
              console.log("SR 파일 읽기 완료 (Data URL).");
              try {
                  // 순수 Base64 문자열 추출
                  srBase64ImageString = dataUrl.substring(dataUrl.indexOf(',') + 1);
                  console.log("SR Base64 추출 완료 (첫 50자):", srBase64ImageString.substring(0, 50) + "...");
                  srStatus.textContent = `파일 준비 완료: ${srSelectedFile.name}. 처리 요청 버튼을 누르세요.`;
                  srUploadButton.disabled = false; // 버튼 활성화
              } catch (e) {
                  console.error("SR Base64 추출 중 오류:", e);
                  srStatus.textContent = "파일 처리 중 오류가 발생했습니다.";
                  srUploadButton.disabled = true;
              }
          };
          reader.onerror = function(errorEvent) {
               console.error("SR 파일 읽기 오류:", errorEvent);
               srStatus.textContent = "파일을 읽는 중 오류가 발생했습니다.";
               srUploadButton.disabled = true;
          };
          reader.readAsDataURL(srSelectedFile);
      } else {
           srStatus.textContent = "파일을 선택해주세요.";
           srUploadButton.disabled = true;
           srSelectedFile = null;
      }
  });
} else { console.warn("SR file input related elements not found."); }

// SR 처리 요청 버튼 클릭
if (srUploadButton && srStatus && srResultImage) {
  srUploadButton.addEventListener('click', () => {
      if (!srSelectedFile || !srBase64ImageString) {
          alert("먼저 SR 처리할 이미지 파일을 선택해주세요.");
          return;
      }

      const token = getCookie("access_token");
      if (!token) {
          alert("로그인이 필요합니다.");
          // 필요시 로그인 페이지로 리다이렉트
          // window.location.href = '/login.html';
          return; // 인증 토큰 없으면 중단
      }

      srStatus.textContent = "SR 처리 요청 중...";
      srUploadButton.disabled = true;
      srResultImage.src = "";

      const payload = {
          filename: srSelectedFile.name, // 요청된 고정 파일명
          image: srBase64ImageString
      };

      // axios 를 사용하여 POST 요청 보내기
      axios.post(`${API_URL}/v1/super-resolution`, payload, { // *** 엔드포인트 수정됨 ***
          headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}` // *** 인증 헤더 추가 ***
          },
          timeout: 60000 // SR 처리가 오래 걸릴 수 있으므로 타임아웃 증가 (예: 60초)
      })
      .then(response => {
          // 성공 응답 처리
          const result = response.data;
          console.log("SR 서버 응답:", result);
          srStatus.textContent = "SR 처리 완료!";

          if (result.image && result.filename) {
               // 결과 이미지 표시 (Data URL 사용)
               let mimeType = 'image/png'; // 기본 PNG 가정
               const lowerFilename = result.filename.toLowerCase();
               if (lowerFilename.endsWith('.jpg') || lowerFilename.endsWith('.jpeg')) {
                   mimeType = 'image/jpeg';
               } else if (lowerFilename.endsWith('.webp')) {
                   mimeType = 'image/webp';
               } // 필요시 다른 포맷 추가

               srResultImage.src = `data:${mimeType};base64,${result.image}`;
               srStatus.textContent = `SR 처리 완료! 결과 파일명: ${result.filename}`;
          } else {
              srStatus.textContent = "SR 처리는 완료되었으나 응답에 이미지 데이터가 없습니다.";
               console.warn("SR 응답에 image 또는 filename 필드가 없습니다:", result);
          }
      })
      .catch(error => {
          // 에러 처리
          console.error('SR 요청 오류:', error);
          let errorMsg = "SR 처리 요청 실패";
          if (error.code === 'ECONNABORTED') {
              errorMsg += " - 요청 시간 초과";
          } else if (error.response) {
              errorMsg += ` (Status: ${error.response.status})`;
              if (error.response.data && error.response.data.detail) {
                   errorMsg += ` - ${error.response.data.detail}`;
              } else if (typeof error.response.data === 'string' && error.response.data.length < 100) {
                   errorMsg += ` - ${error.response.data}`;
              } else {
                   errorMsg += ` - 서버 에러 메시지 확인 필요`;
              }
          } else if (error.request) {
              errorMsg += " - 서버 응답 없음";
          } else {
              errorMsg += ` - ${error.message}`;
          }
          srStatus.textContent = errorMsg;
      })
      .finally(() => {
          // 요청 완료 후 항상 실행
           if (srSelectedFile) {
              srUploadButton.disabled = false; // 버튼 다시 활성화
           }
      });
  });
} else { console.warn("SR upload button or related elements not found."); }


/* ================================================
   초기화 로직 (페이지 로드 시 실행)
================================================ */
window.addEventListener("DOMContentLoaded", async () => {
  console.log("DOM Loaded. Initializing...");

  const token = getCookie("access_token");
  console.log("Initial token check:", token || "No token found");

  // SR 섹션 요소 가져오기 (여기서도 필요)
  const srSectionElement = document.getElementById("srSection");

  // 기본적으로 로그인/회원가입/SR 섹션 상태 설정
  if (loginForm) loginForm.style.display = "block";
  if (signupForm) signupForm.style.display = "none";
  if (showSignupFormButton) showSignupFormButton.style.display = "inline-block";
  if (logoutButton) logoutButton.style.display = "none";
  if (boardSection) boardSection.style.display = "none";
  if (postDetails) postDetails.style.display = "none";
  if (createPostForm) createPostForm.style.display = "none";
  if (srSectionElement) srSectionElement.style.display = "none"; // *** 기본 숨김 ***
  if (loggedUserSpan) loggedUserSpan.textContent = "";

  if (token) {
    console.log("Token found, attempting to verify and load user data...");
    // 토큰이 있으면 일단 로그인된 UI 시도
    loginForm.style.display = "none";
    showSignupFormButton.style.display = "none";
    logoutButton.style.display = "inline-block";
    boardSection.style.display = "block";
    if (srSectionElement) srSectionElement.style.display = "block"; // *** SR 섹션 보이기 ***

    try {
      // 사용자 정보 로드 시도 (토큰 유효성 검증 포함)
      await loadUserName();
      // 사용자 정보 로드 성공 시 게시글 로드
      console.log("User verified, loading board posts...");
      loadBoardPosts();
    } catch (error) {
      // loadUserName 내부에서 이미 로그 찍고 로그아웃 처리함
      console.log("Token verification failed or error loading initial data.");
      // UI는 handleLogout() 에서 로그아웃 상태로 전환됨
    }
  } else {
      // 토큰 없으면 초기 상태 유지 (이미 위에서 설정됨)
      console.log("No token found, showing login form.");
  }
});