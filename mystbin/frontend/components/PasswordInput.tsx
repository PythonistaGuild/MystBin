import { Form, InputGroup } from "react-bootstrap";
import styles from "../styles/PasswordInput.module.css";
import VisibilityOffIcon from "@material-ui/icons/VisibilityOff";
import VisibilityIcon from "@material-ui/icons/Visibility";
import React, { useState } from "react";

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
    <InputGroup className="mb-3">
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
      <InputGroup.Text>
        <span
          className={
            passwordHide
              ? styles.passwordVisibilityTrue
              : styles.passwordVisibilityFalse
          }
          onClick={() => setPasswordHide(!passwordHide)}
        >
          {passwordHide ? <VisibilityIcon /> : <VisibilityOffIcon />}
        </span>
      </InputGroup.Text>
    </InputGroup>
  );
}
