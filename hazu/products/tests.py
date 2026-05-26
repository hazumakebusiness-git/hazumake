from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from unittest.mock import patch

from .models import Game, Product


class VerifyPlayerViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='tester',
            password='password123'
        )
        self.game = Game.objects.create(
            name='Mobile Legends Test',
            short_name='MLBB_TEST',
            slug='mobile-legends-test',
            supplier_game_code='mobilelegends',
            is_active=True,
            checkout_fields=[
                {'name': 'uid', 'label': 'Player ID', 'placeholder': 'Enter player id', 'required': True},
                {'name': 'zoneid', 'label': 'Zone ID', 'placeholder': 'Enter zone id', 'required': False},
            ],
        )

    @patch('hazu.smile_api.verify_player')
    def test_verify_player_accepts_uid_and_zoneid(self, mock_verify_player):
        mock_verify_player.return_value = 'PlayerName'
        self.client.login(username='tester', password='password123')

        url = reverse('verify_player', kwargs={'slug': self.game.slug})
        payload = {
            'uid': '123456789',
            'sid': '1234',
            'productid': 'prod_abc',
        }

        response = self.client.post(
            url,
            data=payload,
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {
            'status': 200,
            'success': True,
            'nickname': 'PlayerName',
            'uid': '123456789',
            'zone': '1234',
        })
        mock_verify_player.assert_called_once_with(
            game_slug='mobilelegends',
            product_id='prod_abc',
            player_uid='123456789',
            player_sid='1234',
        )

    @patch('hazu.smile_api.verify_player')
    def test_verify_player_accepts_userid_and_zoneid_aliases(self, mock_verify_player):
        mock_verify_player.return_value = 'PlayerName'
        self.client.login(username='tester', password='password123')

        url = reverse('verify_player', kwargs={'slug': self.game.slug})
        payload = {
            'userid': '123456789',
            'zoneid': '1234',
            'product_id': 'prod_abc',
        }

        response = self.client.post(
            url,
            data=payload,
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {
            'status': 200,
            'success': True,
            'nickname': 'PlayerName',
            'uid': '123456789',
            'zone': '1234',
        })
        mock_verify_player.assert_called_once_with(
            game_slug='mobilelegends',
            product_id='prod_abc',
            player_uid='123456789',
            player_sid='1234',
        )

    def test_product_detail_renders_verify_player_route_and_productid(self):
        product = Product.objects.create(
            game=self.game,
            name='Test Product',
            smile_product_id='test_product_id',
            type='DIAMOND',
            diamond_amount=100,
            price_coins=100,
            price_inr=100.00,
        )

        self.client.login(username='tester', password='password123')
        response = self.client.get(reverse('product_detail', kwargs={'pk': product.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'const verifyUrl = "/shop/mobile-legends-test/verify-player/";')
        self.assertContains(response, 'name="productid" value="test_product_id"')
        self.assertNotContains(response, 'name="game-slug"')

    @patch('hazu.smile_api.verify_player')
    def test_verify_player_falls_back_to_game_slug_when_supplier_code_missing(self, mock_verify_player):
        mock_verify_player.return_value = 'PlayerName'
        self.game.supplier_game_code = ''
        self.game.save()
        self.client.login(username='tester', password='password123')

        url = reverse('verify_player', kwargs={'slug': self.game.slug})
        payload = {
            'uid': '123456789',
            'sid': '1234',
            'productid': 'prod_abc',
        }

        response = self.client.post(
            url,
            data=payload,
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {
            'status': 200,
            'success': True,
            'nickname': 'PlayerName',
            'uid': '123456789',
            'zone': '1234',
        })
        mock_verify_player.assert_called_once_with(
            game_slug='mobile-legends-test',
            product_id='prod_abc',
            player_uid='123456789',
            player_sid='1234',
        )

    def test_verify_player_requires_uid_and_productid(self):
        self.client.login(username='tester', password='password123')

        url = reverse('verify_player', kwargs={'slug': self.game.slug})
        payload = {
            'sid': '1234',
        }

        response = self.client.post(
            url,
            data=payload,
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {'status': 400, 'success': False, 'message': 'uid and productid are required'})


class SmileOneSignatureTests(TestCase):
    @override_settings(
        SMILE_UID='3268463',
        SMILE_EMAIL='extraofficial144@gmail.com',
        SMILE_KEY='8420b83ef3caccc997fb05c594263e5d',
        SMILE_BASE_URL='https://www.smile.one',
    )
    def test_generate_smileone_sign_matches_expected_format(self):
        from hazu.utils.signature import build_smileone_sign_string, generate_smileone_sign

        payload = {
            'uid': '3268463',
            'email': 'extraofficial144@gmail.com',
            'product': 'mobilelegends',
            'productid': '22590',
            'userid': '123456789',
            'zoneid': '1234',
            'time': '1716086400',
        }
        secret = '8420b83ef3caccc997fb05c594263e5d'
        expected_string = 'email=extraofficial144@gmail.com&product=mobilelegends&productid=22590&time=1716086400&uid=3268463&userid=123456789&zoneid=1234&' + secret
        actual_string = build_smileone_sign_string(payload, secret)
        self.assertEqual(actual_string, expected_string)

        signature = generate_smileone_sign(payload, secret)
        self.assertEqual(signature, 'ea7ff57178b0c3a6702cb2ed061fda8a')

    @override_settings(
        SMILE_UID='3268463',
        SMILE_EMAIL='extraofficial144@gmail.com',
        SMILE_KEY='8420b83ef3caccc997fb05c594263e5d',
        SMILE_BASE_URL='https://www.smile.one',
    )
    def test_smileone_payload_omits_empty_zoneid(self):
        from hazu.services.smileone import _build_payload

        payload = _build_payload({
            'product': 'mobilelegends',
            'productid': '22590',
            'userid': '123456789',
            'zoneid': '',
        })

        self.assertNotIn('zoneid', payload)
        self.assertIn('sign', payload)
        self.assertEqual(payload['uid'], str(payload['uid']).strip())
        self.assertEqual(payload['email'], str(payload['email']).strip())

    @override_settings(
        SMILE_UID='3268463',
        SMILE_EMAIL='extraofficial144@gmail.com',
        SMILE_KEY='8420b83ef3caccc997fb05c594263e5d',
        SMILE_BASE_URL='https://www.smile.one',
    )
    @patch('hazu.services.smileone._http_post_form')
    def test_get_role_request_uses_form_getrole_payload(self, mock_http_post_form):
        mock_http_post_form.return_value = {'status': 200, 'data': {'username': 'PlayerName'}}

        from hazu.services.smileone import get_role
        username = get_role('mobilelegends', '22590', '123456789', '')

        self.assertEqual(username, 'PlayerName')
        mock_http_post_form.assert_called_once()
        called_url, called_payload = mock_http_post_form.call_args[0]
        self.assertEqual(called_url, 'https://www.smile.one/br/smilecoin/api/getrole')
        self.assertEqual(called_payload['product'], 'mobilelegends')
        self.assertEqual(called_payload['productid'], '22590')
        self.assertEqual(called_payload['userid'], '123456789')
        self.assertNotIn('zoneid', called_payload)
        self.assertIn('time', called_payload)
        self.assertIn('sign', called_payload)
        self.assertEqual(set(called_payload.keys()), {'uid', 'email', 'time', 'product', 'productid', 'userid', 'sign'})

    @override_settings(
        SMILE_UID='3268463',
        SMILE_EMAIL='extraofficial144@gmail.com',
        SMILE_KEY='8420b83ef3caccc997fb05c594263e5d',
        SMILE_BASE_URL='https://www.smile.one',
    )
    @patch('hazu.services.smileone._http_post_form')
    def test_get_role_normalizes_mlbb_aliases(self, mock_http_post_form):
        mock_http_post_form.return_value = {'status': 200, 'data': {'username': 'PlayerName'}}

        from hazu.services.smileone import get_role
        username = get_role('Mobile Legends: Bang Bang', '22590', '123456789', '1234')

        self.assertEqual(username, 'PlayerName')
        mock_http_post_form.assert_called_once()
        called_url, called_payload = mock_http_post_form.call_args[0]
        self.assertEqual(called_url, 'https://www.smile.one/br/smilecoin/api/getrole')
        self.assertEqual(called_payload['product'], 'mobilelegends')
        self.assertEqual(called_payload['productid'], '22590')
        self.assertEqual(called_payload['userid'], '123456789')
        self.assertEqual(called_payload['zoneid'], '1234')
        self.assertIn('time', called_payload)
        self.assertIn('sign', called_payload)
        self.assertEqual(set(called_payload.keys()), {'uid', 'email', 'time', 'product', 'productid', 'userid', 'zoneid', 'sign'})

    @override_settings(
        SMILE_UID='3268463',
        SMILE_EMAIL='extraofficial144@gmail.com',
        SMILE_KEY='8420b83ef3caccc997fb05c594263e5d',
        SMILE_BASE_URL='https://www.smile.one/br/smilecoin/api',
        SMILE_API_PREFIX='br/smilecoin/api',
    )
    @patch('hazu.services.smileone._http_post_form')
    def test_get_role_handles_base_url_containing_api_prefix(self, mock_http_post_form):
        mock_http_post_form.return_value = {'status': 200, 'data': {'username': 'PlayerName'}}

        from hazu.services.smileone import get_role
        username = get_role('mobilelegends', '22590', '123456789', '1234')

        self.assertEqual(username, 'PlayerName')
        mock_http_post_form.assert_called_once()
        called_url, called_payload = mock_http_post_form.call_args[0]
        self.assertEqual(called_url, 'https://www.smile.one/br/smilecoin/api/getrole')
        self.assertEqual(called_payload['product'], 'mobilelegends')
        self.assertEqual(called_payload['productid'], '22590')
        self.assertEqual(called_payload['userid'], '123456789')
        self.assertEqual(called_payload['zoneid'], '1234')
        self.assertIn('time', called_payload)
        self.assertIn('sign', called_payload)
        self.assertEqual(set(called_payload.keys()), {'uid', 'email', 'time', 'product', 'productid', 'userid', 'zoneid', 'sign'})

    @override_settings(
        SMILE_UID='3268463',
        SMILE_EMAIL='extraofficial144@gmail.com',
        SMILE_KEY='8420b83ef3caccc997fb05c594263e5d',
        SMILE_BASE_URL='https://www.smile.one',
    )
    def test_parse_smileone_response_detects_html(self):
        from hazu.services.smileone import _parse_smileone_response, SmileOneError

        with self.assertRaises(SmileOneError):
            _parse_smileone_response('<html><body>Cloudflare error</body></html>')
