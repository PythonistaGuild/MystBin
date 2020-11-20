import {Nav, Navbar} from "react-bootstrap";
import React from "react";
import EnhancedEncryptionIcon from '@material-ui/icons/EnhancedEncryption';


export default function OptsBar() {
    return (
        <Navbar>
            <Nav className="ml-auto">
                <EnhancedEncryptionIcon></EnhancedEncryptionIcon>
            </Nav>
        </Navbar>
    );
}