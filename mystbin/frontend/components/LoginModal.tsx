import { Modal } from "react-bootstrap";
import styles from "../styles/Login.module.css";
import LogoMain from "../public/LogoMain";
import DiscordColorIcon from "../icons/DiscordColour";
import GitHubIcon from "@material-ui/icons/GitHub";
import GoogleIcon from "../icons/GoogleIcon";
import { useRouter } from "next/router";

export default function LoginModal({ onHide }: { onHide: () => void }) {
  const router = useRouter();

  return (
    <>
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
              router.push("/");
            }}
          >
            <DiscordColorIcon className={styles.icons} />
          </div>
          <div
            className={styles.iconsContainer}
            onClick={() => {
              router.push("/");
            }}
          >
            <GitHubIcon className={styles.icons} />
          </div>
          <div
            className={styles.iconsContainer}
            onClick={() => {
              router.push("/");
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
            By logging in via one of the provided services above, you agree to our{" "}
            <a href={"/"}>Terms and Conditions</a>,{" "}
            <a href={"/"}>Privacy Policy </a>
            and consent to our <a href={"/"}>Cookie Policy</a>.
          </small>
        </Modal.Footer>
      </Modal>
    </>
  );
}
