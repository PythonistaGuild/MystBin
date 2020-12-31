import { Form } from "react-bootstrap";
import styles from "../styles/EditorTabs.module.css";
import VisibilityOffIcon from "@material-ui/icons/VisibilityOff";
import VisibilityIcon from "@material-ui/icons/Visibility";
import { useState } from "react";

export default function PasswordInput({
  value,
  onChange,
  onSubmit,
}: {
  value: string;
  onChange: (arg0: string) => void;
  onSubmit: (arg0: string) => void;
}) {
  const [passwordHide, setPasswordHide] = useState(true);

  return (
    <Form>
      <Form.Group controlId="pastePassword" className={styles.passwordGroup}>
        <Form.Control
          className={styles.passwordInput}
          type={passwordHide ? "password" : "text"}
          placeholder="Password"
          onChange={(event) => {
            onChange(event.currentTarget.value);
          }}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              onSubmit(value);
            }
          }}
        />
        <span
          className={
            passwordHide
              ? styles.passwordVisibilityTrue
              : styles.passwordVisibilityFalse
          }
          onClick={(e) => setPasswordHide(!passwordHide)}
        >
          {passwordHide ? <VisibilityIcon /> : <VisibilityOffIcon />}
        </span>
      </Form.Group>
    </Form>
  );
}
