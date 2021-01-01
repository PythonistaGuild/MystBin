import {
  Modal,
  Nav,
  Navbar,
  OverlayTrigger,
  Popover,
  Form,
  InputGroup,
  Button,
} from "react-bootstrap";
import React, { useState } from "react";
import EnhancedEncryptionIcon from "@material-ui/icons/EnhancedEncryption";
import HourglassFullIcon from "@material-ui/icons/HourglassFull";
import SaveAltIcon from "@material-ui/icons/SaveAlt";
import EditIcon from "@material-ui/icons/Edit";
import styles from "../styles/OptsBar.module.css";
import { useHotkeys } from "react-hotkeys-hook";
import ExpiryModal from "./ExpiryModal";

export default function OptsBar() {
  const [currentModal, setCurrentModal] = useState(null);
  const [expiryValue, setExpiryValue] = useState([-1, -1, -1]);

  const actions = [
    {
      title: "Save Paste",
      content: "Save this paste and all its files.",
      icon: <SaveAltIcon />,
      callback: () => {
        alert("test!");
      },
      hotKey: "ctrl+s",
    },
    {
      title: "Edit Paste",
      content: "Copy and Edit this paste as a new paste.",
      icon: <EditIcon />,
      callback: () => {
        alert("test2!");
      },
      hotKey: "ctrl+e",
    },
  ];

  const opts = [
    {
      title: "Create Password",
      content: "Create a password for this paste and all its files.",
      optional: true,
      icon: <EnhancedEncryptionIcon />,
      callback: () => alert("test3"),
    },
    {
      title: "Create Expiry",
      content: "Create a expiry date for this paste and all its files.",
      optional: true,
      icon: <HourglassFullIcon />,
      callback: () => {
        setCurrentModal(
          <ExpiryModal
            initialValue={expiryValue}
            onHide={() => {
              setCurrentModal(null);
            }}
            onSubmit={setExpiryValue}
          />
        );
      },
    },
  ];

  actions.forEach(({ callback, hotKey }) => {
    useHotkeys(hotKey, callback);
  });

  return (
    <div>
      {currentModal && currentModal}
      <Navbar className="justify-content-center">
        <Nav className={styles.optsNavContainer}>
          {actions.map(OptsButton)}
          {opts.map(OptsButton)}
        </Nav>
      </Navbar>
    </div>
  );
}

function OptsButton(obj: {
  title: string;
  content: string;
  icon: JSX.Element;
  callback: () => void;
  hotKey?: string;
  optional?: boolean;
}): JSX.Element {
  return (
    <OverlayTrigger
      key={`opt-${obj.title}`}
      placement={"bottom"}
      overlay={
        <Popover id={`opt-${obj.title}`}>
          <Popover.Title className={styles.popoverHeader} as="h3">
            {obj.title}
            {obj.hotKey && (
              <span
                style={{
                  float: "right",
                  color: "rgba(255, 255, 255, .6)",
                }}
              >
                {obj.hotKey}
              </span>
            )}
          </Popover.Title>
          <Popover.Content>
            {obj.content}{" "}
            {obj.optional !== undefined && (
              <strong>{obj.optional ? "Optional" : "Required"}</strong>
            )}
          </Popover.Content>
        </Popover>
      }
    >
      <div className={styles.optsIconContainer} onClick={() => obj.callback()}>
        {obj.icon}
      </div>
    </OverlayTrigger>
  );
}
