import { Modal } from "react-bootstrap";
import styles from "../styles/Login.module.css";
import LogoMain from "../public/LogoMain";
import DiscordColorIcon from "../icons/DiscordColour";
import GitHubIcon from "@material-ui/icons/GitHub";
import GoogleIcon from "../icons/GoogleIcon";
import { useRouter } from "next/router";
import { useState } from "react";
import Popout from "react-popout";
import cookieCutter from "cookie-cutter";

export default function LoginModal({ onHide }: { onHide: () => void }) {
  const router = useRouter();
  const [window, setWindow] = useState(null);

  return (
    <>
      {window ? (
        <Popout
          title={"MystBin - Login"}
          url={window}
          onClosing={() => {
            cookieCutter.set("state", "true");
            setWindow(null);
            router.reload();
          }}
        />
      ) : null}
      <Modal
        show={true}
        onHide={onHide}
        aria-labelledby="contained-modal-title-vcenter"
        centered
        className={styles.loginModal}
      >
        <Modal.Header className={styles.loginModalHeader}>
          <Modal.Title className={styles.loginModalTitle}>
            <LogoMain className={styles.logo} />
            <br />
            Login
          </Modal.Title>
        </Modal.Header>
        <Modal.Body className={styles.loginModalBody}>
          <div
            className={styles.iconsContainer}
            onClick={() => {
              setWindow(
                "https://discord.com/api/oauth2/authorize?client_id=569566608817782824&redirect_uri=https%3A%2F%2Fstaging.mystb.in%2Fdiscord_auth&response_type=code&scope=identify%20email"
              );
            }}
          >
            <DiscordColorIcon className={styles.icons} />
          </div>
          <div
            className={styles.iconsContainer}
            onClick={() => {
              setWindow(
                "https://github.com/login/oauth/authorize?client_id=b7706c70bf211e796c70&redirect_uri=https://staging.mystb.in/github_auth&scope=user"
              );
            }}
          >
            <GitHubIcon className={styles.icons} />
          </div>
          <div
            className={styles.iconsContainer}
            onClick={() => {
              setWindow(
                "https://accounts.google.com/o/oauth2/v2/auth?client_id=441802425406-seonbv5tmcu2htuhgs544imp9rtk0giu.apps.googleusercontent.com&redirect_uri=https://staging.mystb.in/google_auth&response_type=code&scope=https://www.googleapis.com/auth/userinfo.email"
              );
            }}
          >
            <GoogleIcon className={styles.googleIcon} />
          </div>
        </Modal.Body>
        <Modal.Body className={styles.loginModalBody}>
          <small className={styles.iconsText}>Via Discord</small>
          <small className={styles.iconsText}>Via GitHub</small>
          <small className={styles.iconsText}>Via Google</small>
        </Modal.Body>
        <Modal.Footer>
          <small>
            By logging in via one of the provided services above, you agree to
            our <a href={"/"}>Terms and Conditions</a>,{" "}
            <a href={"/"}>Privacy Policy </a>
            and consent to our <a href={"/"}>Cookie Policy</a>.
          </small>
        </Modal.Footer>
      </Modal>
    </>
  );
}
